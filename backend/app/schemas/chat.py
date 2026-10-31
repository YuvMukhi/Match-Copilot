from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    match_id: str = Field(default="match_001")
    team_id: str = Field(default="team_001")
    over: int = Field(default=10, ge=0, le=20)
    message: str = Field(..., min_length=1)
    language: str = Field(default="en")  # "en" or "hinglish"


class EvidencePayload(BaseModel):
    tool_called: str
    title: str
    summary: str
    confidence_note: Optional[str] = None
    table_headers: list[str] = Field(default_factory=list)
    table_rows: list[dict[str, Any]] = Field(default_factory=list)
    raw_data: Optional[dict[str, Any]] = None


class ChatResponse(BaseModel):
    answer: str
    evidence: Optional[EvidencePayload] = None
    over: int
    language: str
    is_out_of_scope: bool = False
