"""Folk-term normalization: Vietnamese folk health phrases -> clinical terms."""
import json
from functools import lru_cache

from src import config
from src.watsonx_client import generate


@lru_cache(maxsize=1)
def glossary() -> dict[str, str]:
    return json.loads(config.GLOSSARY_PATH.read_text("utf-8"))


def match_terms(claim: str) -> list[tuple[str, str]]:
    """Longest-match-first glossary lookup."""
    text, found = claim.lower(), []
    for phrase in sorted(glossary(), key=len, reverse=True):
        if phrase in text:
            found.append((phrase, glossary()[phrase]))
            text = text.replace(phrase, " ")
    return found


def normalize(claim: str) -> tuple[str, str, int]:
    """Return (clinical_query, understood_line, tokens)."""
    terms = match_terms(claim)
    understood = "; ".join(f"{a} → {b}" for a, b in terms)
    expansion = " ".join(b for _, b in terms)
    if config.OFFLINE:
        return f"{claim} {expansion}".strip(), understood, 0
    prompt = (
        "Viết lại tin đồn sức khỏe sau thành một câu truy vấn y khoa ngắn bằng tiếng Việt, "
        "dùng thuật ngữ y khoa chuẩn. Chỉ trả về câu truy vấn.\n"
        f"Gợi ý thuật ngữ: {understood or 'không có'}\nTin đồn: {claim}\nTruy vấn:"
    )
    try:
        text, tokens = generate(prompt, max_tokens=60)
        query = text.strip().splitlines()[0].strip(' "')
    except Exception:
        query, tokens = "", 0
    return f"{query or claim} {expansion}".strip(), understood, tokens
