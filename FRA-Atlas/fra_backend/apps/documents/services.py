"""Pluggable storage / malware-scan / OCR. Backend chosen by settings
(STORAGE_BACKEND, AV_SCANNER, OCR_ENGINE) so dev runs with zero external
services and prod wires S3 + ClamAV + Tesseract by setting env vars.
"""
import hashlib
import logging
from pathlib import Path

from django.conf import settings

logger = logging.getLogger("fra.documents")


# ------------------------------------------------------------- storage -------
class LocalStorage:
    def __init__(self):
        self.root = Path(getattr(settings, "MEDIA_ROOT", settings.BASE_DIR / "media"))
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, key, content):
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return key

    def read(self, key):
        return (self.root / key).read_bytes()

    def signed_url(self, key, expires_seconds=3600):
        return f"/api/v1/documents/local/{key}"


class S3Storage:
    """Real S3 backend (boto3). Uploads with SSE and issues short-lived
    presigned download URLs."""

    def __init__(self):
        import boto3
        self.bucket = settings.AWS_STORAGE_BUCKET_NAME
        self.client = boto3.client("s3", region_name=settings.AWS_S3_REGION_NAME or None)

    def save(self, key, content):
        self.client.put_object(Bucket=self.bucket, Key=key, Body=content,
                               ServerSideEncryption="AES256")
        return key

    def read(self, key):
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()

    def signed_url(self, key, expires_seconds=3600):
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_seconds)


def get_storage():
    if getattr(settings, "STORAGE_BACKEND", "local") == "s3":
        try:
            return S3Storage()
        except Exception as exc:  # misconfig shouldn't crash the request path
            logger.error("S3 storage unavailable, falling back to local: %s", exc)
    return LocalStorage()


# ------------------------------------------------------------ scanning -------
class NoopScanner:
    def scan(self, content):
        if b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE" in content:
            return "INFECTED"
        return "CLEAN"


class ClamAVScanner:
    """Streams the file to a clamd daemon over TCP."""

    def scan(self, content):
        try:
            import clamd
            cd = clamd.ClamdNetworkSocket(host=settings.CLAMAV_HOST,
                                          port=settings.CLAMAV_PORT)
            import io
            result = cd.instream(io.BytesIO(content))
            status = result.get("stream", ("", ""))[0]
            return "INFECTED" if status == "FOUND" else "CLEAN"
        except Exception as exc:
            logger.error("ClamAV unavailable: %s", exc)
            return "ERROR"


def get_scanner():
    if getattr(settings, "AV_SCANNER", "noop") == "clamav":
        return ClamAVScanner()
    return NoopScanner()


# ---------------------------------------------------------------- OCR --------
class NoopOCR:
    def extract_text(self, content, content_type):
        return ""


class TesseractOCR:
    """Tesseract OCR for images; for scanned PDFs render pages first."""

    def extract_text(self, content, content_type):
        try:
            import io

            import pytesseract
            from PIL import Image
            if content_type.startswith("image/"):
                return pytesseract.image_to_string(Image.open(io.BytesIO(content)))
            return ""  # PDF rasterization left to a pdf->image step in prod
        except Exception as exc:
            logger.error("OCR unavailable: %s", exc)
            return ""


def get_ocr():
    if getattr(settings, "OCR_ENGINE", "noop") == "tesseract":
        return TesseractOCR()
    return NoopOCR()


def sha256_of(content):
    return hashlib.sha256(content).hexdigest()
