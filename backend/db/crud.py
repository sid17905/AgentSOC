import json
import logging
from datetime import UTC, datetime
from typing import Optional

from backend.config import utc_now
from backend.db.database import get_connection, init_db
from backend.schemas.incident import (
    IOC,
    MITRETechnique,
    IncidentReport,
    IncidentStatus,
)


logger = logging.getLogger(__name__)


def save_incident(incident: IncidentReport) -> None:
    try:
        init_db()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO incidents (
                    id,
                    status,
                    incident_type,
                    severity,
                    confidence,
                    title,
                    summary,
                    iocs,
                    mitre_techniques,
                    playbook_steps,
                    raw_input,
                    created_at,
                    updated_at,
                    report_markdown,
                    agent_thoughts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident.id,
                    _enum_value(incident.status),
                    _enum_value(incident.incident_type),
                    _enum_value(incident.severity),
                    incident.confidence,
                    incident.title,
                    incident.summary,
                    json.dumps([_model_dict(ioc) for ioc in incident.iocs]),
                    json.dumps(
                        [
                            _model_dict(technique)
                            for technique in incident.mitre_techniques
                        ]
                    ),
                    json.dumps([str(step) for step in incident.playbook_steps]),
                    incident.raw_input,
                    _to_iso_z(incident.created_at),
                    _to_iso_z(incident.updated_at),
                    incident.report_markdown,
                    json.dumps([str(thought) for thought in incident.agent_thoughts]),
                ),
            )
            conn.commit()
    except Exception:
        logger.exception("save_incident failed for incident_id=%s", incident.id)


def get_incident(incident_id: str) -> Optional[IncidentReport]:
    try:
        init_db()
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM incidents WHERE id = ?",
                (incident_id,),
            ).fetchone()
        if row is None:
            return None
        return _row_to_incident(row)
    except Exception:
        logger.exception("get_incident failed for incident_id=%s", incident_id)
        return None


def list_incidents() -> list[IncidentReport]:
    try:
        init_db()
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM incidents ORDER BY created_at DESC"
            ).fetchall()
        return [_row_to_incident(row) for row in rows]
    except Exception:
        logger.exception("list_incidents failed")
        return []


def get_incidents() -> list[IncidentReport]:
    return list_incidents()


def update_incident_status(
    incident_id: str,
    status: IncidentStatus | str,
) -> Optional[IncidentReport]:
    incident = get_incident(incident_id)
    if incident is None:
        return None

    try:
        incident.status = IncidentStatus(_enum_value(status))
        incident.updated_at = utc_now()
        save_incident(incident)
        return get_incident(incident_id)
    except Exception:
        logger.exception("update_incident_status failed for incident_id=%s", incident_id)
        return None


def _row_to_incident(row) -> IncidentReport:
    return IncidentReport(
        id=row["id"],
        status=row["status"],
        incident_type=row["incident_type"],
        severity=row["severity"],
        confidence=row["confidence"],
        title=row["title"],
        summary=row["summary"],
        iocs=[IOC(**item) for item in json.loads(row["iocs"])],
        mitre_techniques=[
            MITRETechnique(**item) for item in json.loads(row["mitre_techniques"])
        ],
        playbook_steps=[str(item) for item in json.loads(row["playbook_steps"])],
        raw_input=row["raw_input"],
        created_at=_from_iso_z(row["created_at"]),
        updated_at=_from_iso_z(row["updated_at"]),
        report_markdown=row["report_markdown"],
        agent_thoughts=[str(item) for item in json.loads(row["agent_thoughts"])],
    )


def _model_dict(model) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    if hasattr(model, "dict"):
        return model.dict()
    return dict(model)


def _enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _to_iso_z(value: datetime | None) -> str:
    if value is None:
        value = utc_now()
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _from_iso_z(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

