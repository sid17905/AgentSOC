import base64
import io
import re

from PIL import Image, ImageFilter

try:
    import pytesseract

    TESSERACT_AVAILABLE = True
except ImportError:
    pytesseract = None
    TESSERACT_AVAILABLE = False


IOC_PATTERNS = {
    "ip_address": re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"),
    "domain": re.compile(
        r"\b(?:[a-zA-Z0-9-]+\.)+(?:com|net|org|io|ru|cn|gov|edu|xyz|onion)\b"
    ),
    "file_path_win": re.compile(r"[A-Za-z]:\\(?:[^\\\s]+\\)*[^\\\s]*"),
    "file_path_unix": re.compile(r"/(?:[a-zA-Z0-9._-]+/)*[a-zA-Z0-9._-]+"),
    "hash_md5_sha": re.compile(r"\b[0-9a-fA-F]{32,64}\b"),
    "cve": re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE),
    "error_keywords": re.compile(
        r"\b(?:error|failed|denied|blocked|exploit|malware|ransomware"
        r"|backdoor|rootkit|exfil|c2|c&c|beacon|dropper|payload)\b",
        re.IGNORECASE,
    ),
}

SECURITY_KEYWORDS = [
    "error",
    "failed",
    "denied",
    "blocked",
    "exploit",
    "malware",
    "ransomware",
    "backdoor",
    "rootkit",
    "exfil",
    "c2",
    "beacon",
    "dropper",
    "payload",
    "privilege",
    "escalation",
    "lateral",
    "persistence",
    "obfuscated",
]


def _rule_based_findings(text: str) -> str:
    """Extract security-relevant observations without an external LLM."""
    findings = []

    for label, pattern in IOC_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            unique_matches = list(dict.fromkeys(matches))[:5]
            findings.append(
                f"{label.replace('_', ' ').title()}: {', '.join(unique_matches)}"
            )

    lowered_text = text.lower()
    keyword_hits = [kw for kw in SECURITY_KEYWORDS if kw in lowered_text]
    if keyword_hits:
        findings.append(f"Security keywords detected: {', '.join(keyword_hits[:8])}")

    if not findings:
        return "No obvious security indicators detected in image text."

    return "\n".join(findings)


def _prepare_image_for_ocr(image: Image.Image) -> Image.Image:
    image = image.convert("RGB")
    width, height = image.size

    if width < 800:
        scale = 800 / width
        image = image.resize((int(width * scale), int(height * scale)), Image.LANCZOS)

    image = image.filter(ImageFilter.SHARPEN)
    return image.convert("L")


def parse_image(base64_content: str, media_type: str = "image/png") -> dict:
    try:
        if media_type not in {"image/png", "image/jpeg", "image/webp", "image/gif"}:
            raise ValueError(f"Unsupported media type: {media_type}")
        if not base64_content:
            raise ValueError("Empty base64 content")

        image_bytes = base64.b64decode(base64_content)
        if len(image_bytes) < 100:
            raise ValueError("Image data too small to be valid")

        image = Image.open(io.BytesIO(image_bytes))

        if TESSERACT_AVAILABLE:
            try:
                extracted_text = pytesseract.image_to_string(
                    _prepare_image_for_ocr(image),
                    lang="eng",
                ).strip()
            except Exception as exc:
                extracted_text = (
                    "[pytesseract is installed, but OCR failed. "
                    "Install/configure the tesseract binary. "
                    f"Detail: {exc}]"
                )
        else:
            extracted_text = (
                "[pytesseract not installed. Install tesseract-ocr and pytesseract "
                "to enable image OCR.]"
            )

        security_findings = _rule_based_findings(extracted_text)
        normalized_text = (
            f"Image OCR complete. Extracted text: {extracted_text[:500]}. "
            f"Security assessment: {security_findings[:300]}"
        )

        return {
            "extracted_text": extracted_text,
            "security_findings": security_findings,
            "normalized_text": normalized_text,
            "error": None,
        }
    except Exception as exc:
        return {
            "extracted_text": "",
            "security_findings": "",
            "normalized_text": "Image parsing failed; using stub.",
            "error": str(exc),
        }


def get_media_type(filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1]
    return {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
    }.get(ext, "image/png")
