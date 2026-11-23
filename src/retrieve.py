"""Dense search, BM25, and hybrid fusion (Reciprocal Rank Fusion)."""
import json
import re
from functools import lru_cache

import numpy as np

from src import config
from src.schema import Chunk
from src.watsonx_client import embed


@lru_cache(maxsize=1)
def _index():
    chunks = json.loads((config.INDEX_DIR / "chunks.json").read_text("utf-8"))
    vectors = np.load(config.INDEX_DIR / "vectors.npy")
    return chunks, vectors


def _tokenize(text: str) -> list[str]:
    try:
        from pyvi import ViTokenizer

        text = ViTokenizer.tokenize(text)
    except Exception:
        pass
    return re.findall(r"\w+", text.lower())


@lru_cache(maxsize=1)
def _bm25():
    from rank_bm25 import BM25Okapi

    chunks, _ = _index()
    return BM25Okapi([_tokenize(c["text"]) for c in chunks])


def _to_chunk(i: int, score: float) -> Chunk:
    c = _index()[0][i]
    return Chunk(source_id=c["source_id"], url=c["url"], text=c["text"], score=float(score))


def dense_ranking(query: str) -> list[tuple[int, float]]:
    _, vectors = _index()
    q = np.array(embed([query], kind="query")[0], dtype="float32")
    q /= np.linalg.norm(q) + 1e-9
    sims = vectors @ q
    order = np.argsort(-sims)
    return [(int(i), float(sims[i])) for i in order]


def bm25_ranking(query: str) -> list[tuple[int, float]]:
    scores = _bm25().get_scores(_tokenize(query))
    order = np.argsort(-scores)
    return [(int(i), float(scores[i])) for i in order]


def dense_search(query: str, k: int = 5) -> list[Chunk]:
    return [_to_chunk(i, s) for i, s in dense_ranking(query)[:k]]


def hybrid_search(query: str, k: int = 5, rrf_k: int = 60) -> list[Chunk]:
    fused: dict[int, float] = {}
    for ranking in (dense_ranking(query), bm25_ranking(query)):
        for rank, (i, _) in enumerate(ranking[:50]):
            fused[i] = fused.get(i, 0.0) + 1.0 / (rrf_k + rank + 1)
    top = sorted(fused.items(), key=lambda x: -x[1])[:k]
    return [_to_chunk(i, s) for i, s in top]


def search(query: str, k: int = 5, hybrid: bool = False) -> list[Chunk]:
    return hybrid_search(query, k) if hybrid else dense_search(query, k)
