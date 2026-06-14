from enum import Enum
from typing import Optional

from pydantic import BaseModel


class InputType(str, Enum):
    LOG = "log"
    PDF = "pdf"
    IMAGE = "image"
    EMAIL = "email"
    JSON = "json"


class AgentInput(BaseModel):
    input_type: InputType
    content: str
    filename: Optional[str] = None
