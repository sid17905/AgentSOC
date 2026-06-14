import re
from datetime import datetime
from email import policy
from email.parser import Parser
from email.utils import getaddresses, parseaddr
from typing import List


URL_PATTERN = r'https?://[^\s"\'<>]+'
_URL_RE = re.compile(URL_PATTERN)
_SUBJECT_KEYWORDS = ("urgent", "verify", "suspended", "click here")
_IP_HOST_RE = re.compile(r'^(?:\d{1,3}\.){3}\d{1,3}$')
_DOMAIN_RE = re.compile(r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b')


def parse_email(raw_email: str) -> dict:
    parsed_at = datetime.utcnow().isoformat() + "Z"
    message = Parser(policy=policy.default).parsestr(raw_email)

    sender_header = message.get("From", "")
    sender_name, sender_address = parseaddr(sender_header)
    sender = sender_address or sender_header
    recipients = _extract_recipients(message)
    subject = message.get("Subject", "") or ""
    body = _extract_body(message)
    attachments = _extract_attachments(message)
    links = _URL_RE.findall(body)
    suspicious_indicators = _suspicious_indicators(
        sender_name=sender_name,
        sender_address=sender_address,
        subject=subject,
        links=links,
    )
    normalized_text = (
        f"[{parsed_at}] Email from {sender} with subject '{subject}'. "
        f"{len(links)} links found. Suspicious: {suspicious_indicators}"
    )

    return {
        "sender": sender,
        "recipients": recipients,
        "subject": subject,
        "body": body,
        "links": links,
        "attachments": attachments,
        "suspicious_indicators": suspicious_indicators,
        "normalized_text": normalized_text,
        "parsed_at": parsed_at,
    }


def _extract_recipients(message) -> List[str]:
    headers = []
    for field in ("To", "Cc", "Bcc"):
        headers.extend(message.get_all(field, []))
    return [address for _, address in getaddresses(headers) if address]


def _extract_body(message) -> str:
    if message.is_multipart():
        plain_parts = []
        fallback_parts = []
        for part in message.walk():
            if part.is_multipart():
                continue
            if part.get_content_disposition() == "attachment":
                continue

            content_type = part.get_content_type()
            content = _part_content(part)
            if not content:
                continue

            if content_type == "text/plain":
                plain_parts.append(content)
            elif content_type == "text/html":
                fallback_parts.append(content)

        return "\n".join(plain_parts or fallback_parts).strip()

    return _part_content(message).strip()


def _part_content(part) -> str:
    try:
        content = part.get_content()
    except Exception:
        payload = part.get_payload(decode=True)
        if payload is None:
            payload = part.get_payload()
        if isinstance(payload, bytes):
            charset = part.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")
        return str(payload or "")

    if isinstance(content, bytes):
        charset = part.get_content_charset() or "utf-8"
        return content.decode(charset, errors="replace")
    return str(content or "")


def _extract_attachments(message) -> List[str]:
    attachments = []
    for part in message.walk() if message.is_multipart() else [message]:
        filename = part.get_filename()
        if filename:
            attachments.append(filename)
    return attachments


def _suspicious_indicators(
    sender_name: str,
    sender_address: str,
    subject: str,
    links: List[str],
) -> List[str]:
    indicators = []

    for link in links:
        host = _url_host(link)
        if not host:
            continue
        if _IP_HOST_RE.match(host):
            _add_indicator(indicators, f"link uses IP address: {link}")
        if host.count(".") > 3:
            _add_indicator(indicators, f"link has excessive subdomains: {link}")

    subject_lower = subject.lower()
    for keyword in _SUBJECT_KEYWORDS:
        if keyword in subject_lower:
            _add_indicator(indicators, f"subject contains '{keyword}'")

    if _sender_domain_mismatch(sender_name, sender_address):
        _add_indicator(indicators, "sender domain does not match display name domain")

    return indicators


def _url_host(link: str) -> str:
    without_scheme = re.sub(r'^https?://', "", link, flags=re.IGNORECASE)
    host = without_scheme.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    return host.rsplit("@", 1)[-1].split(":", 1)[0].lower()


def _sender_domain_mismatch(sender_name: str, sender_address: str) -> bool:
    sender_domain = _email_domain(sender_address)
    if not sender_domain or not sender_name:
        return False

    display_email_domain = _email_domain(parseaddr(sender_name)[1])
    display_domains = _DOMAIN_RE.findall(sender_name)
    candidate_domains = [display_email_domain] if display_email_domain else []
    candidate_domains.extend(display_domains)

    for domain in candidate_domains:
        if domain.lower() != sender_domain:
            return True
    return False


def _email_domain(address: str) -> str:
    if not address or "@" not in address:
        return ""
    return address.rsplit("@", 1)[-1].lower()


def _add_indicator(indicators: List[str], indicator: str) -> None:
    if indicator not in indicators:
        indicators.append(indicator)
