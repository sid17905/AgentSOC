# Member D Integration Notes

Member D owns multimodal image parsing, incident report generation, Slack alert delivery, and GitHub Issues ticket creation.

## Files

- `backend/parsers/image_parser.py`
- `backend/reporting/report_generator.py`
- `backend/reporting/templates/incident_report.md`
- `backend/delivery/slack_notifier.py`
- `backend/delivery/github_issues.py`
- `tests/test_image_parser.py`
- `tests/test_report_generator.py`

## Dependencies

Install the Python packages in `backend/requirements.txt`.

For real OCR, install the Tesseract system binary:

- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- macOS: `brew install tesseract`
- Ubuntu/Debian: `sudo apt install tesseract-ocr`

If Tesseract is missing, `parse_image` still returns a graceful fallback instead of crashing.

## Orchestrator Hook

Member A should add this near the end of `run_agent`, after the incident fields are populated:

```python
from backend.reporting.report_generator import generate_report

incident.report_markdown = generate_report(incident)
incident.agent_thoughts.append("[Report] Incident report generated.")

from backend.delivery.slack_notifier import send_slack_alert

slack_ok = await send_slack_alert(incident)
if slack_ok:
    incident.agent_thoughts.append("[Slack] Alert sent to SecOps channel.")
else:
    incident.agent_thoughts.append("[Slack] Alert printed to console (no webhook).")
```

## Approval Hook

Member A should call this inside the approve endpoint:

```python
from backend.delivery.github_issues import create_issue

issue = create_issue(incident)
if issue["issue_number"]:
    incident.agent_thoughts.append(
        f"[GitHub] Issue created: #{issue['issue_number']} {issue['url']}"
    )
else:
    incident.agent_thoughts.append(f"[GitHub] Issue skipped: {issue['error']}")
```

## PDF Endpoint

The PDF download endpoint should call:

```python
from backend.reporting.report_generator import generate_pdf_report
```

Return the bytes from `generate_pdf_report(incident)` with content type `application/pdf`.

## Optional Environment Variables

```env
SLACK_WEBHOOK_URL=
GITHUB_TOKEN=
GITHUB_REPO=owner/repo-name
OLLAMA_MODEL=llama3
```

Slack and GitHub are optional. If they are not configured, the code falls back gracefully for demos.
