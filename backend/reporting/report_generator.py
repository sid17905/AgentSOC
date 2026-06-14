import html
import os

from backend.config import get_settings, utc_now
from backend.schemas.incident import IncidentReport


TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__),
    "templates",
    "incident_report.md",
)


def _markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def generate_report(incident: IncidentReport) -> str:
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as template_file:
        template = template_file.read()

    ioc_rows = ""
    for ioc in incident.iocs:
        reputation = ioc.reputation or "Pending"
        confidence = f"{int(ioc.confidence * 100)}%"
        ioc_rows += (
            f"| {_markdown_cell(ioc.type)} | `{_markdown_cell(ioc.value)}` | "
            f"{confidence} | {_markdown_cell(reputation)} |\n"
        )
    if not ioc_rows:
        ioc_rows = "| - | No IOCs extracted | - | - |\n"

    mitre_rows = ""
    for technique in incident.mitre_techniques:
        url = (
            "https://attack.mitre.org/techniques/"
            f"{technique.technique_id.replace('.', '/')}"
        )
        mitre_rows += (
            f"| [{_markdown_cell(technique.technique_id)}]({url}) | "
            f"{_markdown_cell(technique.technique_name)} | "
            f"{_markdown_cell(technique.tactic)} |\n"
        )
    if not mitre_rows:
        mitre_rows = "| - | No techniques mapped | - |\n"

    playbook_steps = ""
    for index, step in enumerate(incident.playbook_steps, 1):
        playbook_steps += f"{index}. {step}\n"
    if not playbook_steps:
        playbook_steps = "No playbook steps generated."

    agent_thoughts = ""
    for thought in incident.agent_thoughts:
        agent_thoughts += f"- {thought}\n"
    if not agent_thoughts:
        agent_thoughts = "No agent log available."

    raw_input = incident.raw_input or ""
    raw_input_preview = raw_input[:1000]
    if len(raw_input) > 1000:
        raw_input_preview += "\n... [truncated]"

    replacements = {
        "{TITLE}": incident.title or "Untitled Incident",
        "{INCIDENT_ID}": incident.id,
        "{GENERATED_AT}": utc_now().strftime("%Y-%m-%d %H:%M UTC"),
        "{SEVERITY}": incident.severity.value,
        "{STATUS}": incident.status.value.replace("_", " ").title(),
        "{CONFIDENCE}": str(int(incident.confidence * 100)),
        "{SUMMARY}": incident.summary or "No summary available.",
        "{INCIDENT_TYPE}": incident.incident_type.value.replace("_", " ").title(),
        "{CREATED_AT}": str(incident.created_at)[:19],
        "{UPDATED_AT}": str(incident.updated_at)[:19],
        "{IOC_TABLE_ROWS}": ioc_rows,
        "{MITRE_TABLE_ROWS}": mitre_rows,
        "{PLAYBOOK_STEPS}": playbook_steps,
        "{RAW_INPUT}": raw_input_preview,
        "{AGENT_THOUGHTS}": agent_thoughts,
        "{OLLAMA_MODEL}": get_settings().ollama_model,
    }

    filled = template
    for placeholder, value in replacements.items():
        filled = filled.replace(placeholder, value)

    return filled


def generate_pdf_report(incident: IncidentReport) -> bytes:
    """Convert the markdown report to a simple PDF using reportlab."""
    import io

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    markdown_text = generate_report(incident)
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    story = []

    for line in markdown_text.splitlines():
        clean = html.escape(line.replace("**", "").replace("__", ""))
        if not line.strip():
            story.append(Spacer(1, 4 * mm))
        elif line.startswith("# "):
            story.append(Paragraph(clean[2:], styles["Heading1"]))
        elif line.startswith("## "):
            story.append(Paragraph(clean[3:], styles["Heading2"]))
        else:
            story.append(Paragraph(clean, styles["Normal"]))

    document.build(story)
    return buffer.getvalue()
