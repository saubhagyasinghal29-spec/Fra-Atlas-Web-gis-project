"""Detect file type from magic bytes, not the client-supplied Content-Type
(which is spoofable). Closes audit finding R9."""

def sniff_content_type(content: bytes) -> str | None:
    if content[:5] == b"%PDF-":
        return "application/pdf"
    if content[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    return None
