from datetime import datetime
from enum import Enum
from typing import List, Optional
import uuid

from pydantic import BaseModel


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
    id: str = None
    status: IncidentStatus = IncidentStatus.PENDING
    incident_type: IncidentType = IncidentType.UNKNOWN
    severity: Severity = Severity.P3
    confidence: float = 0.0
    title: str = ""
    summary: str = ""
    iocs: List[IOC] = []
    mitre_techniques: List[MITRETechnique] = []
    playbook_steps: List[str] = []
    raw_input: str = ""
    created_at: datetime = None
    updated_at: datetime = None
    report_markdown: Optional[str] = None
    agent_thoughts: List[str] = []

    def model_post_init(self, __context):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow()
        if not self.updated_at:
            self.updated_at = datetime.utcnow()
