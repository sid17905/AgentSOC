import asyncio
import base64
import inspect
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
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
from backend.schemas import AgentInput, IncidentReport, IncidentStatus, InputType


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    del app
    ingest_task = None
    if settings.auto_ingest_enabled:
        ingest_task = asyncio.create_task(_auto_ingest_loop())
    try:
        yield
    finally:
        if ingest_task:
            ingest_task.cancel()
            try:
                await ingest_task
            except asyncio.CancelledError:
                pass


app = FastAPI(title="CSIRT Autopilot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

incidents: dict[str, IncidentReport] = {}


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
    incident = incidents.get(id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


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
    del data
    return _detect_input_type_from_name(file.filename or "", file.content_type or "")


def _detect_input_type_from_name(filename: str, content_type: str = "") -> InputType:
    filename = filename.lower()
    content_type = content_type.lower()

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
    return _build_agent_input_from_bytes(
        filename=file.filename or "upload",
        data=data,
        content_type=file.content_type or "",
    )


def _build_agent_input_from_bytes(
    filename: str,
    data: bytes,
    content_type: str = "",
) -> AgentInput:
    input_type = _detect_input_type_from_name(filename, content_type)
    if input_type in {InputType.PDF, InputType.IMAGE}:
        content = base64.b64encode(data).decode("ascii")
    else:
        content = data.decode("utf-8", errors="replace")
    return AgentInput(input_type=input_type, content=content, filename=filename)


async def _submit_for_analysis(
    agent_input: AgentInput,
    source: str = "api",
) -> IncidentReport:
    incident = IncidentReport(
        status=IncidentStatus.ANALYZING,
        raw_input=agent_input.content,
    )
    incident.agent_thoughts = [
        f"[{utc_now().isoformat()}] Analysis started from {source}."
    ]
    incidents[incident.id] = incident
    await manager.broadcast(
        {"type": "incident_update", "data": incident.model_dump(mode="json")}
    )
    asyncio.create_task(run_agent(agent_input, incident, manager.broadcast))
    return incident


def _unique_destination(directory: Path, filename: str) -> Path:
    destination = directory / filename
    if not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    timestamp = utc_now().strftime("%Y%m%d%H%M%S")
    return directory / f"{stem}-{timestamp}{suffix}"


async def _ingest_file(path: Path) -> str:
    if not path.is_file():
        return "skipped"
    if path.stat().st_size > settings.auto_ingest_max_file_size_bytes:
        raise ValueError(
            f"{path.name} exceeds AUTO_INGEST_MAX_FILE_SIZE_BYTES "
            f"({settings.auto_ingest_max_file_size_bytes})"
        )

    data = await asyncio.to_thread(path.read_bytes)
    agent_input = _build_agent_input_from_bytes(path.name, data)
    incident = await _submit_for_analysis(agent_input, source=f"auto-ingest:{path.name}")

    archive_dir = Path(settings.auto_ingest_archive_dir)
    archive_dir.mkdir(parents=True, exist_ok=True)
    destination = _unique_destination(archive_dir, path.name)
    await asyncio.to_thread(shutil.move, str(path), str(destination))
    return incident.id


async def _auto_ingest_loop() -> None:
    ingest_dir = Path(settings.auto_ingest_dir)
    error_dir = Path(settings.auto_ingest_error_dir)
    ingest_dir.mkdir(parents=True, exist_ok=True)
    error_dir.mkdir(parents=True, exist_ok=True)

    while True:
        for path in sorted(ingest_dir.iterdir()):
            if not path.is_file():
                continue
            try:
                incident_id = await _ingest_file(path)
                print(f"[Auto ingest] {path.name} submitted as incident {incident_id}")
            except Exception as exc:
                print(f"[Auto ingest] Failed to ingest {path.name}: {exc}")
                destination = _unique_destination(error_dir, path.name)
                try:
                    await asyncio.to_thread(shutil.move, str(path), str(destination))
                except Exception as move_exc:
                    print(f"[Auto ingest] Failed to move {path.name}: {move_exc}")
        await asyncio.sleep(settings.auto_ingest_interval_seconds)


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


@app.post("/api/v1/analyze")
async def analyze(agent_input: AgentInput):
    incident = await _submit_for_analysis(agent_input)
    return {"incident_id": incident.id}


@app.get("/api/v1/incidents")
async def list_incidents():
    return sorted(incidents.values(), key=lambda item: item.created_at, reverse=True)


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
    await manager.broadcast(
        {"type": "incident_update", "data": incident.model_dump(mode="json")}
    )
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
    await manager.broadcast(
        {"type": "incident_update", "data": incident.model_dump(mode="json")}
    )
    return incident


@app.websocket("/ws/incidents")
async def incidents_websocket(ws: WebSocket):
    await manager.connect(ws)
    try:
        await ws.send_json(
            [incident.model_dump(mode="json") for incident in incidents.values()]
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


@app.get("/api/v1/ingestion/status")
async def ingestion_status():
    return {
        "enabled": settings.auto_ingest_enabled,
        "directory": settings.auto_ingest_dir,
        "archive_directory": settings.auto_ingest_archive_dir,
        "error_directory": settings.auto_ingest_error_dir,
        "interval_seconds": settings.auto_ingest_interval_seconds,
        "max_file_size_bytes": settings.auto_ingest_max_file_size_bytes,
    }


@app.get("/api/v1/incidents/{id}/report/pdf")
async def incident_report_pdf(id: str):
    incident = _incident_or_404(id)
    try:
        from backend.reporting.report_generator import generate_pdf_report

        pdf_bytes = generate_pdf_report(incident)
    except Exception:
        pdf_bytes = _fallback_pdf_report(incident)
    return Response(content=pdf_bytes, media_type="application/pdf")
