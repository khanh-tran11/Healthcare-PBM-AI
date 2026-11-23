"""Configuration and feature flags. Secrets come only from .env."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

WATSONX_APIKEY = os.getenv("WATSONX_APIKEY", "").strip()
WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "").strip()
WATSONX_MODEL_ID = os.getenv("WATSONX_MODEL_ID", "meta-llama/llama-3-3-70b-instruct")
WATSONX_EMBED_MODEL_ID = os.getenv("WATSONX_EMBED_MODEL_ID", "intfloat/multilingual-e5-large")
PRICE_PER_1K_TOKENS = float(os.getenv("PRICE_PER_1K_TOKENS", "0") or 0)

# Offline mode: no watsonx key -> local hashing embeddings + rule-based judge.
OFFLINE = not (WATSONX_APIKEY and WATSONX_PROJECT_ID) or os.getenv("OFFLINE", "") == "1"

SOURCES_DIR = ROOT / "data" / "sources"
GLOSSARY_PATH = ROOT / "data" / "glossary.json"
CLAIMS_PATH = ROOT / "data" / "eval_claims.jsonl"
INDEX_DIR = ROOT / "index"


@dataclass(frozen=True)
class Flags:
    hybrid: bool = False
    folk: bool = False
    agent: bool = False

    @classmethod
    def parse(cls, text: str) -> "Flags":
        parts = {p.strip() for p in (text or "").split(",") if p.strip()}
        return cls(hybrid="hybrid" in parts, folk="folk" in parts, agent="agent" in parts)


# Default for the app: everything on.
APP_FLAGS = Flags(hybrid=True, folk=True, agent=True)
