import asyncio
import inspect
import json
import re
import time
from typing import Callable

try:
    import ollama
except Exception:
    ollama = None

from backend.agent.state import AgentState
from backend.agent.tools import TOOL_DESCRIPTIONS, execute_tool
from backend.config import get_settings, utc_now
from backend.schemas.agent_input import AgentInput
from backend.schemas.incident import (
    IOC,
    MITRETechnique,
    IncidentReport,
    IncidentStatus,
    IncidentType,
    Severity,
)


settings = get_settings()

SYSTEM_PROMPT = """
You are CSIRT Autopilot, an AI security analyst. Analyze the incident
and use the available tools step by step. Respond ONLY with valid JSON.

AVAILABLE TOOLS:
{tool_descriptions}

PREVIOUS TOOL RESULTS:
{tool_results_so_far}

CURRENT INCIDENT DATA:
{incident_text}

If you need to call a tool, respond EXACTLY:
{{"action": "tool", "tool": "<tool_name>", "input": {{...}} }}

If analysis is complete, respond EXACTLY:
{{
  "action": "done",
  "incident_type": "<ransomware|phishing|data_exfiltration|lateral_movement|brute_force|unknown>",
  "severity": "<P1|P2|P3|P4>",
  "confidence": <0.0-1.0>,
  "title": "<short title>",
  "summary": "<2-3 sentences>",
  "iocs": [{{"type":"ip","value":"...","confidence":0.9}}],
  "mitre_techniques": [{{"technique_id":"T1059","technique_name":"...","tactic":"..."}}],
  "playbook_steps": ["Step 1:...", "Step 2:..."]
}}

IMPORTANT: Output ONLY valid JSON. No markdown, no explanation, no backticks.
Start with {{ and end with }}.
"""


def log_thought(incident: IncidentReport, msg: str):
    ts = utc_now().strftime("[%H:%M:%S UTC]")
    incident.agent_thoughts.append(f"{ts} {msg}")
    incident.updated_at = utc_now()


def classify_rule_based(text: str) -> dict:
    text_lower = text.lower()
    if any(w in text_lower for w in ["encrypt", "ransom", "locked", "bitcoin"]):
        itype, sev, conf = "ransomware", "P1", 0.75
    elif any(w in text_lower for w in ["phish", "click here", "verify", "suspended"]):
        itype, sev, conf = "phishing", "P2", 0.70
    elif any(w in text_lower for w in ["exfil", "upload", "transfer", "data leak"]):
        itype, sev, conf = "data_exfiltration", "P2", 0.65
    elif any(w in text_lower for w in ["lateral", "psexec", "wmi", "pass-the-hash"]):
        itype, sev, conf = "lateral_movement", "P2", 0.68
    elif any(
        w in text_lower
        for w in ["brute", "failed login", "failed password", "bad credentials"]
    ):
        itype, sev, conf = "brute_force", "P3", 0.72
    else:
        itype, sev, conf = "unknown", "P3", 0.40
    return {
        "incident_type": itype,
        "severity": sev,
        "confidence": conf,
        "title": f"Possible {itype.replace('_', ' ').title()} Detected",
        "summary": (
            f"Rule-based classification: {itype}. Manual review recommended."
        ),
        "playbook_steps": [],
        "iocs": [],
        "mitre_techniques": [],
    }


def _extract_json_object(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _coerce_incident_type(value) -> IncidentType:
    normalized = str(value or IncidentType.UNKNOWN.value).lower().replace(" ", "_")
    try:
        return IncidentType(normalized)
    except ValueError:
        return IncidentType.UNKNOWN


def _coerce_severity(value) -> Severity:
    normalized = str(value or Severity.P3.value).upper()
    try:
        return Severity(normalized)
    except ValueError:
        return Severity.P3


def _coerce_confidence(value) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, confidence))


def _coerce_iocs(values) -> list[IOC]:
    if not isinstance(values, list):
        return []
    iocs = []
    for item in values:
        if not isinstance(item, dict):
            continue
        try:
            iocs.append(IOC(**item))
        except Exception:
            continue
    return iocs


def _coerce_mitre_techniques(values) -> list[MITRETechnique]:
    if not isinstance(values, list):
        return []
    techniques = []
    for item in values:
        if not isinstance(item, dict):
            continue
        try:
            techniques.append(MITRETechnique(**item))
        except Exception:
            continue
    return techniques


def _coerce_strings(values) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item) for item in values if item is not None]


def _apply_agent_result(incident: IncidentReport, result: dict):
    incident.incident_type = _coerce_incident_type(result.get("incident_type"))
    incident.severity = _coerce_severity(result.get("severity"))
    incident.confidence = _coerce_confidence(result.get("confidence"))
    incident.title = str(result.get("title") or "Security Incident Detected")
    incident.summary = str(result.get("summary") or "Manual review recommended.")
    incident.iocs = _coerce_iocs(result.get("iocs"))
    incident.mitre_techniques = _coerce_mitre_techniques(
        result.get("mitre_techniques")
    )
    incident.playbook_steps = _coerce_strings(result.get("playbook_steps"))
    incident.updated_at = utc_now()


async def _broadcast_incident(broadcast_fn: Callable, incident: IncidentReport):
    message = {"type": "incident_update", "data": incident.model_dump(mode="json")}
    result = broadcast_fn(message)
    if inspect.isawaitable(result):
        await result


def _model_content(response) -> str:
    if isinstance(response, dict):
        return response.get("message", {}).get("content", "")
    message = getattr(response, "message", None)
    if isinstance(message, dict):
        return message.get("content", "")
    content = getattr(message, "content", None)
    return content or ""


def _call_ollama(prompt: str):
    if hasattr(ollama, "Client"):
        client = ollama.Client(host=settings.ollama_base_url)
        return client.chat(
            model=settings.ollama_model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.1, "num_predict": 800},
        )
    return ollama.chat(
        model=settings.ollama_model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.1, "num_predict": 800},
    )


async def run_agent(
    agent_input: AgentInput,
    incident: IncidentReport,
    broadcast_fn: Callable,
) -> IncidentReport:
    state = AgentState(incident=incident, started_at=time.time())
    tool_results: list[dict] = []
    completed = False
    fallback_reason = ""

    if ollama is None:
        fallback_reason = "Ollama package is not installed."
        log_thought(incident, f"[Ollama] {fallback_reason}")
    else:
        while state.should_continue and state.iteration < state.max_iterations:
            elapsed = time.time() - state.started_at
            if elapsed > state.time_limit_seconds:
                fallback_reason = (
                    f"Agent hit {state.time_limit_seconds}s limit."
                )
                log_thought(
                    incident,
                    f"[Timeout] Agent hit {state.time_limit_seconds}s limit.",
                )
                break

            state.iteration += 1
            prompt = SYSTEM_PROMPT.format(
                tool_descriptions=TOOL_DESCRIPTIONS,
                tool_results_so_far=json.dumps(tool_results, default=str),
                incident_text=agent_input.content,
            )

            try:
                response = await asyncio.to_thread(_call_ollama, prompt)
                parsed = _extract_json_object(_model_content(response).strip())
            except ConnectionRefusedError as exc:
                fallback_reason = f"Ollama connection refused: {exc}"
                log_thought(incident, f"[Ollama] {fallback_reason}")
                break
            except Exception as exc:
                fallback_reason = f"Ollama or JSON parsing failed: {exc}"
                log_thought(incident, f"[Ollama] {fallback_reason}")
                break

            action = parsed.get("action")
            if action == "tool":
                tool_name = str(parsed.get("tool", ""))
                tool_input = parsed.get("input") or {}
                if not isinstance(tool_input, dict):
                    tool_input = {}
                result = execute_tool(tool_name, tool_input)
                tool_results.append(
                    {"tool": tool_name, "input": tool_input, "result": result}
                )
                log_thought(incident, f"[{tool_name}] {result[:120]}")
                await _broadcast_incident(broadcast_fn, incident)
                continue

            if action == "done":
                _apply_agent_result(incident, parsed)
                completed = True
                state.should_continue = False
                break

            fallback_reason = f"Unknown agent action: {action}"
            log_thought(incident, f"[Agent] {fallback_reason}")
            break

    if not completed:
        if not fallback_reason:
            fallback_reason = "Max iterations reached, finalizing."
            log_thought(incident, "[Agent] Max iterations reached, finalizing.")
        fallback = classify_rule_based(agent_input.content)
        _apply_agent_result(incident, fallback)
        log_thought(incident, f"[Fallback] {fallback_reason}")

    incident.status = IncidentStatus.AWAITING_APPROVAL
    incident.updated_at = utc_now()
    await _broadcast_incident(broadcast_fn, incident)
    return incident
