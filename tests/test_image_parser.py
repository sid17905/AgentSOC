import base64
import io

from PIL import Image, ImageDraw

from backend.parsers.image_parser import get_media_type, parse_image


def make_test_image_b64(text: str = "192.168.1.100 CVE-2021-44228") -> str:
    image = Image.new("RGB", (400, 80), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text((10, 25), text, fill=(0, 0, 0))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def test_parse_image_returns_dict():
    result = parse_image(make_test_image_b64())
    assert isinstance(result, dict)
    assert "extracted_text" in result
    assert "security_findings" in result
    assert "normalized_text" in result


def test_parse_image_no_crash_on_empty():
    result = parse_image("")
    assert result["error"] is not None


def test_get_media_type():
    assert get_media_type("screenshot.png") == "image/png"
    assert get_media_type("photo.JPG") == "image/jpeg"
    assert get_media_type("unknown.bmp") == "image/png"
