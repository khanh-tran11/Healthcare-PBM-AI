"""Check the watsonx connection: python scripts/smoke_test.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import config  # noqa: E402
from src.watsonx_client import embed, generate  # noqa: E402

if config.OFFLINE:
    print("OFFLINE mode: WATSONX_APIKEY / WATSONX_PROJECT_ID missing in .env. App runs with local fallback.")
    print("embedding dim:", len(embed(["xin chào"])[0]))
    sys.exit(0)
text, tokens = generate("Trả lời bằng tiếng Việt, một câu: uống kháng sinh có chữa được cảm cúm không?", 80)
print("LLM:", text.strip(), f"({tokens} tokens)")
print("embedding dim:", len(embed(["xin chào"], kind="query")[0]))
