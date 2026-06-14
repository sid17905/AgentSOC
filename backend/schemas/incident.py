from datetime import datetime
from enum import Enum
from typing import List, Optional
import uuid

from pydantic import BaseModel, Field

from backend.config import utc_now


class Severity(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class IncidentType(str, Enum):
    RANSOMWARE = "ransomware"
    PHISHING = "phishing"
    DATA_EXFILTRATION = "data_exfiltration"
    LATERAL_MOVEMENT = "lateral_movement"
    BRUTE_FORCE = "brute_force"
    UNKNOWN = "unknown"


class IncidentStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"


class IOC(BaseModel):
    type: str
    value: str
    confidence: float
    reputation: Optional[str] = None


class MITRETechnique(BaseModel):
    technique_id: str
    technique_name: str
    tactic: str


class IncidentReport(BaseModel):
    id: Optional[str] = None
    status: IncidentStatus = IncidentStatus.PENDING
    incident_type: IncidentType = IncidentType.UNKNOWN
    severity: Severity = Severity.P3
    confidence: float = 0.0
    title: str = ""
    summary: str = ""
    iocs: List[IOC] = Field(default_factory=list)
    mitre_techniques: List[MITRETechnique] = Field(default_factory=list)
    playbook_steps: List[str] = Field(default_factory=list)
    raw_input: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    report_markdown: Optional[str] = None
    agent_thoughts: List[str] = Field(default_factory=list)

    def model_post_init(self, __context):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = utc_now()
        if not self.updated_at:
            self.updated_at = utc_now()
