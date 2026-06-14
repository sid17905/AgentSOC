import asyncio
import base64
import inspect
from contextlib import asynccontextmanager
from typing import List

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from backend.agent.orchestrator import run_agent
from backend.config import get_settings, utc_now
from backend.db import crud
from backend.db.database import init_db
from backend.ingestion.mock_source import mock_ingestion
from backend.schemas import AgentInput, IncidentReport, IncidentStatus, InputType


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="CSIRT Autopilot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ts() -> str:
    return utc_now().strftime("[%H:%M:%S UTC]")


def _now_z() -> str:
    return utc_now().isoformat()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active_connections:
            self.active_connections.remove(ws)

    async def broadcast(self, message: dict):
        dead = []
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except Exception:
                dead.append(conn)
        for conn in dead:
            self.disconnect(conn)


manager = ConnectionManager()


def _incident_or_404(id: str) -> IncidentReport:
    incident = crud.get_incident(id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


async def _save_and_broadcast_incident(incident: IncidentReport) -> None:
    crud.save_incident(incident)
    await manager.broadcast(
        {"type": "incident_update", "data": incident.model_dump(mode="json")}
    )


async def _maybe_create_github_issue(incident: IncidentReport):
    try:
        from backend.delivery.github_issues import create_issue
    except Exception:
        return

    try:
        result = create_issue(incident)
        if inspect.isawaitable(result):
            await result
    except Exception as exc:
        incident.agent_thoughts.append(
            f"{ts()} [GitHub Issues] Issue creation skipped: {exc}"
        )
        incident.updated_at = utc_now()


def _detect_input_type(file: UploadFile, data: bytes) -> InputType:
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()

    if filename.endswith(".pdf") or content_type == "application/pdf":
        return InputType.PDF
    if content_type.startswith("image/") or filename.endswith(
        (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff")
    ):
        return InputType.IMAGE
    if filename.endswith((".eml", ".msg")) or content_type == "message/rfc822":
        return InputType.EMAIL
    if filename.endswith(".json") or content_type == "application/json":
        return InputType.JSON
    return InputType.LOG


def _build_agent_input(file: UploadFile, data: bytes) -> AgentInput:
    input_type = _detect_input_type(file, data)
    if input_type in {InputType.PDF, InputType.IMAGE}:
        content = base64.b64encode(data).decode("ascii")
    else:
        content = data.decode("utf-8", errors="replace")
    return AgentInput(input_type=input_type, content=content, filename=file.filename)


def _fallback_pdf_report(incident: IncidentReport) -> bytes:
    lines = [
        "CSIRT Autopilot Incident Report",
        "",
        f"ID: {incident.id}",
        f"Status: {incident.status.value}",
        f"Type: {incident.incident_type.value}",
        f"Severity: {incident.severity.value}",
        f"Confidence: {incident.confidence:.2f}",
        f"Title: {incident.title}",
        "",
        "Summary:",
        incident.summary,
        "",
        "Playbook Steps:",
        *[f"- {step}" for step in incident.playbook_steps],
    ]
    escaped_lines = [
        line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        for line in lines[:42]
    ]
    rendered_lines = "\n".join(f"({line}) Tj T*" for line in escaped_lines)
    stream = f"BT /F1 11 Tf 72 760 Td 14 TL\n{rendered_lines}\nET"
    stream_bytes = stream.encode("latin-1", errors="replace")
    header = b"%PDF-1.4\n"
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n",
        (
            b"4 0 obj << /Length "
            + str(len(stream_bytes)).encode("ascii")
            + b" >> stream\n"
            + stream_bytes
            + b"\nendstream endobj\n"
        ),
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
    ]
    offsets = []
    body = b""
    cursor = len(header)
    for obj in objects:
        offsets.append(cursor)
        body += obj
        cursor += len(obj)
    xref_at = len(header) + len(body)
    xref = b"xref\n0 6\n0000000000 65535 f \n"
    xref += b"".join(f"{offset:010d} 00000 n \n".encode("ascii") for offset in offsets)
    trailer = (
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(xref_at).encode("ascii")
        + b"\n%%EOF\n"
    )
    return header + body + xref + trailer


async def submit_for_analysis(agent_input: AgentInput) -> dict:
    incident = IncidentReport(
        status=IncidentStatus.ANALYZING,
        raw_input=agent_input.content,
    )
    incident.agent_thoughts = [f"[{utc_now().isoformat()}] Analysis started."]

    async def persist_and_broadcast(message: dict) -> None:
        crud.save_incident(incident)
        await manager.broadcast(message)

    await _save_and_broadcast_incident(incident)
    asyncio.create_task(run_agent(agent_input, incident, persist_and_broadcast))
    return {"incident_id": incident.id}


@app.post("/api/v1/analyze")
async def analyze(agent_input: AgentInput):
    return await submit_for_analysis(agent_input)


@app.post("/api/v1/ingestion/mock/once")
async def ingest_mock_once():
    return await mock_ingestion.ingest_once(submit_for_analysis)


@app.post("/api/v1/ingestion/mock/start")
async def start_mock_ingestion(interval_seconds: float = 30.0, limit: int | None = 8):
    return mock_ingestion.start(
        submit_for_analysis,
        interval_seconds=interval_seconds,
        limit=limit,
    )


@app.post("/api/v1/ingestion/mock/stop")
async def stop_mock_ingestion():
    return await mock_ingestion.stop()


@app.get("/api/v1/ingestion/mock/status")
async def get_mock_ingestion_status():
    return mock_ingestion.status()


@app.get("/api/v1/incidents")
async def list_incidents():
    return crud.list_incidents()


@app.get("/api/v1/incidents/{id}")
async def get_incident(id: str):
    return _incident_or_404(id)


@app.post("/api/v1/incidents/{id}/approve")
async def approve_incident(id: str):
    incident = _incident_or_404(id)
    now = _now_z()
    incident.status = IncidentStatus.APPROVED
    incident.updated_at = utc_now()
    incident.agent_thoughts.append(f"[{now}] Analyst approved incident.")
    await _maybe_create_github_issue(incident)
    await _save_and_broadcast_incident(incident)
    return incident


@app.post("/api/v1/incidents/{id}/reject")
async def reject_incident(id: str):
    incident = _incident_or_404(id)
    now = _now_z()
    incident.status = IncidentStatus.REJECTED
    incident.updated_at = utc_now()
    incident.agent_thoughts.append(
        f"[{now}] Analyst rejected - queued for re-analysis."
    )
    await _save_and_broadcast_incident(incident)
    return incident


@app.websocket("/ws/incidents")
async def incidents_websocket(ws: WebSocket):
    await manager.connect(ws)
    try:
        await ws.send_json(
            [
                incident.model_dump(mode="json")
                for incident in crud.list_incidents()
            ]
        )
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)


@app.post("/api/v1/upload")
async def upload(file: UploadFile = File(...)):
    data = await file.read()
    return _build_agent_input(file, data)


@app.get("/api/v1/incidents/{id}/report/pdf")
async def incident_report_pdf(id: str):
    incident = _incident_or_404(id)
    try:
        from backend.reporting.report_generator import generate_pdf_report

        pdf_bytes = generate_pdf_report(incident)
    except Exception:
        pdf_bytes = _fallback_pdf_report(incident)
    return Response(content=pdf_bytes, media_type="application/pdf")
