"""Tests for src/judge.py — citation index normalisation, see_doctor flag, offline verdict."""
import json
from unittest.mock import patch

import pytest

from src.judge import _llm_judge, _not_enough, judge
from src.schema import Chunk


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _chunk(text: str, source_id: str = "vac-xin") -> Chunk:
    return Chunk(source_id=source_id, url="https://example.com", text=text)


# ---------------------------------------------------------------------------
# Test: 1-based citation indices are shifted to 0-based
# ---------------------------------------------------------------------------

def test_llm_judge_1based_citations_are_shifted():
    """When the LLM returns 1-based indices they must resolve to the correct chunks."""
    chunks = [
        _chunk("Vắc-xin không gây tự kỷ. Không có mối liên hệ giữa vắc-xin và tự kỷ."),
        _chunk("Tỷ lệ tiêm chủng cao giúp đạt miễn dịch cộng đồng."),
    ]
    # LLM returns index 1 (1-based) meaning the first chunk
    llm_response = json.dumps({
        "label": "sai",
        "confidence": 0.9,
        "explanation_vi": "Vắc-xin không gây tự kỷ.",
        "cited": [1],          # 1-based → should resolve to chunks[0]
        "see_doctor": False,
    })

    with patch("src.judge.generate", return_value=(llm_response, 50)):
        with patch("src.judge.config") as mock_cfg:
            mock_cfg.OFFLINE = False
            verdict = _llm_judge("Vắc-xin gây tự kỷ", chunks, "")

    assert verdict.label == "sai"
    assert len(verdict.citations) == 1
    assert verdict.citations[0].text == chunks[0].text  # first chunk, not second


def test_llm_judge_0based_citations_unchanged():
    """When the LLM returns 0-based indices they must not be shifted."""
    chunks = [
        _chunk("Không có mối liên hệ giữa vắc-xin và tự kỷ."),
        _chunk("Miễn dịch cộng đồng cần tỷ lệ tiêm cao."),
    ]
    llm_response = json.dumps({
        "label": "sai",
        "confidence": 0.85,
        "explanation_vi": "Không có bằng chứng.",
        "cited": [0],          # already 0-based
        "see_doctor": False,
    })

    with patch("src.judge.generate", return_value=(llm_response, 40)):
        with patch("src.judge.config") as mock_cfg:
            mock_cfg.OFFLINE = False
            verdict = _llm_judge("Vắc-xin gây tự kỷ", chunks, "")

    assert verdict.citations[0].text == chunks[0].text


# ---------------------------------------------------------------------------
# Test: see_doctor=True when claim contains danger keyword and no evidence
# ---------------------------------------------------------------------------

def test_not_enough_see_doctor_true_for_dot_quy():
    """_not_enough must set see_doctor=True when claim contains 'đột quỵ'."""
    verdict = _not_enough([], "", "offline", claim="Bị đột quỵ nên chích máu ngón tay")
    assert verdict.see_doctor is True
    assert verdict.label == "chua_du_bang_chung"


def test_not_enough_see_doctor_false_for_safe_claim():
    """_not_enough must leave see_doctor=False for a benign claim."""
    verdict = _not_enough([], "", "offline", claim="Uống nước chanh giúp đẹp da")
    assert verdict.see_doctor is False


def test_judge_no_chunks_dangerous_claim():
    """judge() with empty chunks and a danger keyword → see_doctor=True."""
    with patch("src.judge.config") as mock_cfg:
        mock_cfg.OFFLINE = True
        verdict = judge("Bị tai biến có nên dùng thuốc nam không", [])
    assert verdict.see_doctor is True
    assert verdict.label == "chua_du_bang_chung"


# ---------------------------------------------------------------------------
# Test: offline rule judge returns "sai" for vaccine-autism claim
# ---------------------------------------------------------------------------

def test_offline_vaccine_autism_is_sai():
    """Offline judge should return 'sai' for a vaccine-autism claim
    when the retrieved chunk contains a clear refutation cue."""
    chunks = [
        _chunk(
            "Không có mối liên hệ giữa vắc-xin và tự kỷ. "
            "Nhiều nghiên cứu lớn không tìm thấy bằng chứng nào về điều này.",
            source_id="vac-xin",
        )
    ]
    with patch("src.judge.config") as mock_cfg:
        mock_cfg.OFFLINE = True
        verdict = judge("Vắc-xin MMR gây tự kỷ ở trẻ em", chunks)

    assert verdict.label == "sai"
    assert verdict.citations, "offline judge must cite at least one chunk"
