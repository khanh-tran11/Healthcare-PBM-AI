"""Pydantic models shared by the pipeline, eval and UI."""
from typing import Literal, Optional

from pydantic import BaseModel, Field

Label = Literal["dung", "sai", "gay_hieu_lam", "chua_du_bang_chung"]

LABEL_VI = {
    "dung": "Đúng",
    "sai": "Sai",
    "gay_hieu_lam": "Gây hiểu lầm",
    "chua_du_bang_chung": "Chưa đủ bằng chứng",
}


class Chunk(BaseModel):
    source_id: str
    url: str
    text: str
    score: float = 0.0


class Verdict(BaseModel):
    label: Label
    confidence: float = Field(ge=0.0, le=1.0)
    understood: str = ""
    explanation_vi: str
    citations: list[Chunk] = []
    retrieved: list[Chunk] = []
    see_doctor: bool = False
    retried_query: Optional[str] = None
    latency_ms: int = 0
    tokens: int = 0
    mode: str = "watsonx"
