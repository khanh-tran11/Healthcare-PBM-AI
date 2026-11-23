"""Thin wrapper over IBM watsonx.ai (LLM + embeddings), with an offline fallback for embeddings."""
import hashlib
import math
import re
from functools import lru_cache

from src import config


@lru_cache(maxsize=1)
def _credentials():
    from ibm_watsonx_ai import Credentials

    return Credentials(url=config.WATSONX_URL, api_key=config.WATSONX_APIKEY)


@lru_cache(maxsize=1)
def _llm():
    from ibm_watsonx_ai.foundation_models import ModelInference

    return ModelInference(
        model_id=config.WATSONX_MODEL_ID,
        credentials=_credentials(),
        project_id=config.WATSONX_PROJECT_ID,
    )


@lru_cache(maxsize=1)
def _embedder():
    from ibm_watsonx_ai.foundation_models import Embeddings

    return Embeddings(
        model_id=config.WATSONX_EMBED_MODEL_ID,
        credentials=_credentials(),
        project_id=config.WATSONX_PROJECT_ID,
        params={"truncate_input_tokens": 512},
    )


def generate(prompt: str, max_tokens: int = 400) -> tuple[str, int]:
    """Return (text, total_tokens). Uses the chat API, falls back to text generation."""
    if config.OFFLINE:
        raise RuntimeError("generate() called in offline mode")
    model = _llm()
    params = {"max_tokens": max_tokens, "temperature": 0}
    try:
        resp = model.chat(messages=[{"role": "user", "content": prompt}], params=params)
        text = resp["choices"][0]["message"]["content"]
        tokens = int(resp.get("usage", {}).get("total_tokens", 0))
        return text, tokens
    except Exception:  # older models or SDKs without chat
        resp = model.generate(
            prompt=prompt, params={"max_new_tokens": max_tokens, "decoding_method": "greedy"}
        )
        r = resp["results"][0]
        return r["generated_text"], int(r.get("generated_token_count", 0)) + int(
            r.get("input_token_count", 0)
        )


_DIM = 512


def _hash_embed(text: str) -> list[float]:
    """Offline fallback: hashed bag of words and bigrams, L2-normalised."""
    toks = re.findall(r"\w+", text.lower())
    feats = toks + [a + "_" + b for a, b in zip(toks, toks[1:])]
    vec = [0.0] * _DIM
    for f in feats:
        h = int(hashlib.md5(f.encode()).hexdigest(), 16)
        vec[h % _DIM] += 1.0 if (h >> 9) % 2 else -1.0
    n = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / n for v in vec]


def embed(texts: list[str], kind: str = "passage") -> list[list[float]]:
    """kind is 'passage' for documents and 'query' for questions (e5 prefixes)."""
    if config.OFFLINE:
        return [_hash_embed(t) for t in texts]
    prefix = "query: " if kind == "query" else "passage: "
    if "e5" not in config.WATSONX_EMBED_MODEL_ID:
        prefix = ""
    out: list[list[float]] = []
    for i in range(0, len(texts), 100):
        out.extend(_embedder().embed_documents(texts=[prefix + t for t in texts[i : i + 100]]))
    return out
