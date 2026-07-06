"""Authentication: JWT login with account lockout + TOTP MFA.

Flow:
  POST /auth/login/      {username, password}
     -> 423 if locked; 401 on bad creds (increments failure count / locks at 5)
     -> 202 + mfa_challenge token  if MFA enabled (then call /auth/mfa-verify/)
     -> 200 + {access, refresh}    otherwise
  POST /auth/mfa-setup/  (authenticated) -> {secret, provisioning_uri}; sets mfa_enabled
  POST /auth/mfa-verify/ {mfa_challenge, otp_code} -> {access, refresh}
"""
from datetime import timedelta

import pyotp
from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

User = get_user_model()


def _tokens_for(user):
    refresh = RefreshToken.for_user(user)
    refresh["username"] = user.username
    refresh["role"] = user.designation
    refresh["assigned_states"] = user.assigned_states
    refresh["assigned_districts"] = user.assigned_districts
    return {"access_token": str(refresh.access_token), "refresh_token": str(refresh)}


class FRALoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = User.objects.filter(username=username).first()
        if user and user.is_locked:
            return Response({"detail": "Account locked. Try again later."},
                            status=status.HTTP_423_LOCKED)

        authed = authenticate(username=username, password=password)
        if authed is None:
            if user:
                user.register_failed_login()
            return Response({"detail": "Invalid credentials"},
                            status=status.HTTP_401_UNAUTHORIZED)

        authed.register_successful_login()
        if authed.mfa_enabled:
            challenge = AccessToken.for_user(authed)
            challenge["mfa_pending"] = True
            challenge.set_exp(lifetime=timedelta(minutes=5))
            return Response({"mfa_required": True, "mfa_challenge": str(challenge)},
                            status=status.HTTP_202_ACCEPTED)
        return Response(_tokens_for(authed))


class MFASetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        secret = pyotp.random_base32()
        user.mfa_secret = secret
        user.mfa_enabled = True
        user.save(update_fields=["mfa_secret", "mfa_enabled"])
        uri = pyotp.TOTP(secret).provisioning_uri(
            name=user.username, issuer_name="FRA Atlas")
        return Response({"secret": secret, "provisioning_uri": uri})


class MFAVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        challenge = request.data.get("mfa_challenge")
        otp_code = request.data.get("otp_code", "")
        if not challenge:
            return Response({"detail": "mfa_challenge required"}, status=400)
        try:
            token = AccessToken(challenge)
            if not token.get("mfa_pending"):
                return Response({"detail": "Invalid challenge"}, status=400)
            user = User.objects.get(id=token["sub"])
        except Exception:
            return Response({"detail": "Invalid or expired challenge"}, status=400)

        if not pyotp.TOTP(user.mfa_secret).verify(otp_code, valid_window=1):
            user.register_failed_login()
            return Response({"detail": "Invalid OTP"}, status=status.HTTP_401_UNAUTHORIZED)
        user.register_successful_login()
        return Response(_tokens_for(user))


class LogoutView(APIView):
    """Revoke a refresh token (adds it to the blacklist)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from rest_framework_simplejwt.exceptions import TokenError
        from rest_framework_simplejwt.tokens import RefreshToken as RT
        token = request.data.get("refresh_token")
        if not token:
            return Response({"detail": "refresh_token required"}, status=400)
        try:
            RT(token).blacklist()
        except TokenError:
            return Response({"detail": "Invalid or already-revoked token"}, status=400)
        return Response({"detail": "Logged out; token revoked."})
