import os
from datetime import datetime

import httpx

from backend.schemas.incident import IncidentReport


SEVERITY_LABEL = {
    "P1": "CRITICAL",
    "P2": "HIGH",
    "P3": "MEDIUM",
    "P4": "LOW",
}


def _build_console_summary(incident: IncidentReport) -> str:
    severity = SEVERITY_LABEL.get(incident.severity.value, incident.severity.value)
    ioc_list = ", ".join(ioc.value for ioc in incident.iocs[:3]) or "None"
    return (
        f"\n{'=' * 60}\n"
        f"[CSIRT ALERT - Console Fallback] {datetime.utcnow().strftime('%H:%M:%S UTC')}\n"
        f"  Severity:   {severity} ({incident.severity.value})\n"
        f"  Type:       {incident.incident_type.value}\n"
        f"  Title:      {incident.title or 'New Incident'}\n"
        f"  Confidence: {int(incident.confidence * 100)}%\n"
        f"  IOCs:       {ioc_list}\n"
        f"  Summary:    {(incident.summary or '')[:120]}\n"
        f"  ID:         {incident.id}\n"
        f"{'=' * 60}\n"
    )


async def send_slack_alert(incident: IncidentReport) -> bool:
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    if not webhook_url:
        print(_build_console_summary(incident))
        print("[Slack] SLACK_WEBHOOK_URL not set; printed to console instead.")
        return False

    ioc_count = len(incident.iocs)
    top_iocs = ", ".join(ioc.value for ioc in incident.iocs[:3])
    if len(incident.iocs) > 3:
        top_iocs += f" (+{len(incident.iocs) - 3} more)"

    header_text = f"CSIRT Alert: {incident.title or 'New Incident'}"[:149]
    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": header_text},
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{incident.severity.value}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Type:*\n{incident.incident_type.value}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Confidence:*\n{int(incident.confidence * 100)}%",
                    },
                    {"type": "mrkdwn", "text": f"*IOCs Found:*\n{ioc_count}"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{incident.summary or 'No summary available.'}",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Top IOCs:*\n`{top_iocs}`"
                        if top_iocs
                        else "*Top IOCs:*\nNone identified"
                    ),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*Next Step:*\n"
                        "Review and approve in CSIRT Autopilot dashboard.\n"
                        f"Incident ID: `{incident.id}`"
                    ),
                },
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            "CSIRT Autopilot "
                            f"(Ollama/{os.getenv('OLLAMA_MODEL', 'llama3')}) | "
                            f"{str(incident.created_at)[:19]} UTC"
                        ),
                    }
                ],
            },
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
        print(f"[Slack] Alert sent for incident {incident.id}")
        return True
    except Exception as exc:
        print(f"[Slack] Failed: {exc}. Falling back to console.")
        print(_build_console_summary(incident))
        return False
