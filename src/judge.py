"""LLM judge on watsonx: claim + retrieved chunks -> cited Verdict (JSON).
Offline fallback: a transparent rule-based judge, clearly labelled in the UI."""
import json
import re

from pydantic import BaseModel, Field, ValidationError

from src import config
from src.schema import Chunk, Verdict
from src.watsonx_client import generate

PROMPT = """Bạn là trợ lý kiểm chứng tin sức khỏe cho người cao tuổi Việt Nam.
Chỉ dựa vào các ĐOẠN NGUỒN dưới đây (Bộ Y tế, WHO, bệnh viện). Không dùng kiến thức ngoài nguồn.

TIN ĐỒN: {claim}
ĐÃ HIỂU (từ dân gian → y khoa): {understood}

ĐOẠN NGUỒN:
{sources}

Chọn đúng một nhãn:
- "dung": nguồn xác nhận tin này đúng
- "sai": nguồn bác bỏ tin này
- "gay_hieu_lam": có phần đúng nhưng dễ khiến người đọc làm sai
- "chua_du_bang_chung": nguồn không đề cập đủ để kết luận

Trả lời CHỈ bằng JSON, không thêm chữ nào khác:
{{"label": "...", "confidence": 0.0-1.0, "explanation_vi": "tối đa 2 câu ngắn, dễ hiểu, không thuật ngữ", "cited": [số thứ tự đoạn nguồn đã dùng], "see_doctor": true/false}}
"see_doctor" là true nếu tin liên quan dấu hiệu nguy hiểm (đột quỵ, ung thư, sốt xuất huyết...) hoặc làm theo tin có thể gây hại."""


class _Raw(BaseModel):
    label: str
    confidence: float = Field(default=0.5, ge=0, le=1)
    explanation_vi: str = ""
    cited: list[int] = []
    see_doctor: bool = False


def _parse(text: str) -> _Raw:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON object in model output")
    raw = _Raw.model_validate(json.loads(m.group(0)))
    if raw.label not in ("dung", "sai", "gay_hieu_lam", "chua_du_bang_chung"):
        raise ValueError(f"bad label {raw.label}")
    return raw


_DANGER_KEYWORDS = ("đột quỵ", "tai biến", "ung thư", "sốt xuất huyết", "khó thở", "co giật")


def _not_enough(chunks: list[Chunk], understood: str, mode: str, tokens: int = 0, claim: str = "") -> Verdict:
    text = (claim + " " + understood).lower()
    dangerous = any(k in text for k in _DANGER_KEYWORDS)
    return Verdict(
        label="chua_du_bang_chung",
        confidence=0.3,
        understood=understood,
        explanation_vi="Nguồn tin cậy hiện có chưa đủ để kết luận về tin này. Bạn nên hỏi bác sĩ trước khi làm theo.",
        retrieved=chunks,
        see_doctor=dangerous,
        tokens=tokens,
        mode=mode,
    )


def _llm_judge(claim: str, chunks: list[Chunk], understood: str) -> Verdict:
    sources = "\n".join(f"[{i}] ({c.source_id}) {c.text}" for i, c in enumerate(chunks))
    prompt = PROMPT.format(claim=claim, understood=understood or "không có", sources=sources)
    total = 0
    for _ in range(2):  # one retry on bad JSON
        text, tokens = generate(prompt, max_tokens=300)
        total += tokens
        try:
            raw = _parse(text)
            break
        except (ValueError, ValidationError, json.JSONDecodeError):
            continue
    else:
        return _not_enough(chunks, understood, "watsonx", total, claim)
    indices = raw.cited
    # Shift to 0-based if every index looks 1-based (all in 1..len)
    if indices and all(1 <= i <= len(chunks) for i in indices):
        indices = [i - 1 for i in indices]
    cited = [chunks[i] for i in indices if 0 <= i < len(chunks)]
    if not cited and raw.label != "chua_du_bang_chung":
        return _not_enough(chunks, understood, "watsonx", total, claim)  # guardrail: no citation, no verdict
    return Verdict(
        label=raw.label,
        confidence=raw.confidence,
        understood=understood,
        explanation_vi=raw.explanation_vi,
        citations=cited,
        retrieved=chunks,
        see_doctor=raw.see_doctor,
        tokens=total,
        mode="watsonx",
    )


_REFUTE = ("không có tác dụng", "không nên", "không được", "tuyệt đối không", "không phải",
           "không thể", "là sai", "sai lầm", "không chữa", "không có cơ sở", "không giúp",
           "không có mối liên hệ", "không dùng", "không có bằng chứng", "không làm",
           "không gây", "không tự ý")
_UNPROVEN = ("chưa có bằng chứng", "chưa được chứng minh", "chưa đủ bằng chứng")
_DANGER = ("đột quỵ", "tai biến", "ung thư", "sốt xuất huyết", "corticoid")


def _rule_judge(claim: str, chunks: list[Chunk], understood: str) -> Verdict:
    """Offline mode only. Finds the source sentence that best overlaps the claim and
    looks for refutation cues. Transparent but much weaker than the LLM judge."""
    words = {w for w in re.findall(r"\w+", (claim + " " + understood).lower()) if len(w) > 2}
    best, best_overlap, best_chunk = "", 0, None
    for c in chunks:
        for sent in re.split(r"(?<=[.!?])\s+", c.text):
            overlap = len(words & set(re.findall(r"\w+", sent.lower())))
            if overlap > best_overlap:
                best, best_overlap, best_chunk = sent, overlap, c
    if best_chunk is None or best_overlap < 2:
        return _not_enough(chunks, understood, "offline", claim=claim)
    s = best.lower()
    if any(k in s for k in _UNPROVEN):
        label, conf = "chua_du_bang_chung", 0.5
    elif any(k in s for k in _REFUTE):
        label, conf = "sai", min(0.9, 0.4 + 0.1 * best_overlap)
    else:
        label, conf = "dung", min(0.8, 0.3 + 0.1 * best_overlap)
    danger = any(k in (claim + understood).lower() for k in _DANGER)
    return Verdict(
        label=label,
        confidence=conf,
        understood=understood,
        explanation_vi=f"Theo nguồn {best_chunk.source_id}: \"{best.strip()[:220]}\"",
        citations=[best_chunk],
        retrieved=chunks,
        see_doctor=danger,
        mode="offline",
    )


def judge(claim: str, chunks: list[Chunk], understood: str = "") -> Verdict:
    if not chunks:
        return _not_enough(chunks, understood, "offline" if config.OFFLINE else "watsonx", claim=claim)
    if config.OFFLINE:
        return _rule_judge(claim, chunks, understood)
    return _llm_judge(claim, chunks, understood)
