"""Tests for src/folk.py — glossary-based folk-term normalization."""
import pytest

from src.folk import match_terms, normalize


def test_match_terms_trung_gio():
    """'trúng gió' is in the glossary and should be matched."""
    matches = match_terms("Bị trúng gió thì cạo gió là khỏi")
    keys = [k for k, _ in matches]
    assert "trúng gió" in keys


def test_match_terms_cao_huyet_ap():
    """'huyết áp cao' maps to tăng huyết áp."""
    matches = match_terms("Người bị huyết áp cao nên uống nước dừa")
    mapping = dict(matches)
    assert "huyết áp cao" in mapping
    assert "tăng huyết áp" in mapping["huyết áp cao"]


def test_match_terms_no_overlap():
    """Claim with no glossary terms returns an empty list."""
    assert match_terms("Hôm nay trời đẹp") == []


def test_normalize_offline_expands_query(monkeypatch):
    """In offline mode normalize() appends the clinical expansion to the claim."""
    import src.config as cfg
    monkeypatch.setattr(cfg, "OFFLINE", True)

    query, understood, tokens = normalize("Bị tai biến thì nên chích máu đầu ngón tay")

    # Both folk terms must appear in understood
    assert "tai biến" in understood
    assert "chích máu đầu ngón tay" in understood
    # Clinical expansions must appear in the query
    assert "đột quỵ" in query
    # Offline → no LLM call → 0 tokens
    assert tokens == 0


def test_normalize_offline_two_terms(monkeypatch):
    """'tiểu đường' and 'cao máu' are both normalized in one call."""
    import src.config as cfg
    monkeypatch.setattr(cfg, "OFFLINE", True)

    _, understood, _ = normalize("Người tiểu đường bị cao máu không nên uống thuốc")

    assert "tiểu đường" in understood
    assert "cao máu" in understood
