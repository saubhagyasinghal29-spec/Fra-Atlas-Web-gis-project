"""Column-level encryption for PII with key versioning.

Ciphertext format on disk:  ``v{version}:{fernet_token}``. The active key
version (settings.ENCRYPTION_ACTIVE_VERSION) is used for writes; any version in
settings.ENCRYPTION_KEYS can be used for reads, so quarterly key rotation is a
matter of adding a new key + bumping the active version while retaining old keys
to decrypt historical rows.

Keys are 32-byte urlsafe-base64 Fernet keys. In production they come from a
secrets manager / KMS, never source. The dev default below is clearly insecure.
"""
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models

# Dev-only default key (deterministic so the build runs without config).
_DEV_KEY = "2b80PNHyJROYAZhUjOkGXyOKftzi7IRbMY0qg3XwqAU="  # dev-only Fernet key; provide real keys via env in prod


def _keyring():
    keys = getattr(settings, "ENCRYPTION_KEYS", None) or {1: _DEV_KEY}
    return {int(v): Fernet(k.encode() if isinstance(k, str) else k) for v, k in keys.items()}


def _active_version():
    return int(getattr(settings, "ENCRYPTION_ACTIVE_VERSION", 1))


def encrypt(plaintext: str) -> str:
    if plaintext is None or plaintext == "":
        return plaintext
    version = _active_version()
    token = _keyring()[version].encrypt(plaintext.encode()).decode()
    return f"v{version}:{token}"


def decrypt(stored: str) -> str:
    if not stored or ":" not in stored or not stored.startswith("v"):
        return stored  # legacy/plaintext passthrough
    version_str, token = stored.split(":", 1)
    version = int(version_str[1:])
    fernet = _keyring().get(version)
    if not fernet:
        return stored
    try:
        return fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        return stored


class EncryptedCharField(models.CharField):
    """Transparently encrypts on write, decrypts on read. Not exact-match
    queryable (use a separate blind-index column if lookups are required)."""

    def from_db_value(self, value, expression, connection):
        return decrypt(value)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return encrypt(value)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # store ciphertext, which can be much longer than the plaintext
        kwargs["max_length"] = max(kwargs.get("max_length") or 0, 255)
        return name, path, args, kwargs
