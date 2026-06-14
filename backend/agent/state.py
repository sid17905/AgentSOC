from dataclasses import dataclass, field
from typing import List

from backend.schemas.incident import IncidentReport


@dataclass
class AgentState:
    incident: IncidentReport
    iteration: int = 0
    max_iterations: int = 10
    should_continue: bool = True
    pending_tool_calls: List[dict] = field(default_factory=list)
    enrichment_done: bool = False
    classification_done: bool = False
    playbook_done: bool = False
    started_at: float = 0.0
    time_limit_seconds: int = 60
