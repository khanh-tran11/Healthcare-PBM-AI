"""Check the watsonx connection step by step: python scripts/smoke_test.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import config  # noqa: E402

HINTS = {
    "401": "API key rejected: create a new key at cloud.ibm.com/iam/apikeys and paste it into .env.",
    "403": "Key works but has no access to this project, or the project has no watsonx.ai Runtime "
    "associated (project > Manage > Services & integrations).",
    "404": "Project ID or model not found: check WATSONX_PROJECT_ID, and that the model exists in this region.",
    "model": "Model not available in this region/plan: change WATSONX_MODEL_ID / WATSONX_EMBED_MODEL_ID in .env.",
}


def hint(err: Exception) -> str:
    msg = str(err)
    for code, text in HINTS.items():
        if code in msg:
            return text
    if "Name or service not known" in msg or "ConnectionError" in msg or "nodename" in msg:
        return "Cannot reach WATSONX_URL: it must match your project's region, e.g. https://us-south.ml.cloud.ibm.com (Dallas)."
    return "See the error above."


def step(name, fn):
    try:
        out = fn()
        print(f"[OK]   {name}: {out}")
    except Exception as e:  # noqa: BLE001
        print(f"[FAIL] {name}: {type(e).__name__}: {str(e)[:300]}")
        print(f"       -> {hint(e)}")
        sys.exit(1)


print("URL:", config.WATSONX_URL)
print("API key set:", bool(config.WATSONX_APIKEY), "| project id set:", bool(config.WATSONX_PROJECT_ID))
if config.OFFLINE:
    print("OFFLINE mode: WATSONX_APIKEY / WATSONX_PROJECT_ID missing in .env, or OFFLINE=1 is set.")
    sys.exit(1)

from src.watsonx_client import _credentials, embed, generate  # noqa: E402


def _token():
    from ibm_watsonx_ai import APIClient

    client = APIClient(_credentials(), project_id=config.WATSONX_PROJECT_ID)
    return f"connected, SDK {client.version}"


step("1. login + project", _token)
step("2. LLM " + config.WATSONX_MODEL_ID,
     lambda: generate("Trả lời một câu: uống kháng sinh có chữa được cảm cúm không?", 60)[0].strip()[:120])
step("3. embeddings " + config.WATSONX_EMBED_MODEL_ID,
     lambda: f"dim {len(embed(['xin chào'], kind='query')[0])}")
print("All good. Now run: python -m src.ingest")
