"""Load data/sources/*.md, chunk, embed, and save the index. Run: python -m src.ingest"""
import json

import numpy as np

from src import config
from src.watsonx_client import embed

CHUNK, OVERLAP = 500, 100


def load_sources() -> list[dict]:
    docs = []
    for path in sorted(config.SOURCES_DIR.glob("*.md")):
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        if not lines:
            continue
        url = lines[0].strip()
        if not url.startswith("http"):
            url, body = "", "\n".join(lines)
        else:
            body = "\n".join(lines[1:])
        docs.append({"source_id": path.stem, "url": url, "text": " ".join(body.split())})
    return docs


def chunk(text: str) -> list[str]:
    out, i = [], 0
    while i < len(text):
        out.append(text[i : i + CHUNK])
        i += CHUNK - OVERLAP
    return out


def main() -> None:
    chunks = [
        {"source_id": d["source_id"], "url": d["url"], "text": piece}
        for d in load_sources()
        for piece in chunk(d["text"])
    ]
    if not chunks:
        raise SystemExit("No sources found in data/sources/*.md")
    vectors = np.array(embed([c["text"] for c in chunks], kind="passage"), dtype="float32")
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-9
    config.INDEX_DIR.mkdir(exist_ok=True)
    (config.INDEX_DIR / "chunks.json").write_text(json.dumps(chunks, ensure_ascii=False), "utf-8")
    np.save(config.INDEX_DIR / "vectors.npy", vectors)
    (config.INDEX_DIR / "meta.json").write_text(json.dumps({"offline": config.OFFLINE}), "utf-8")
    mode = "offline hashing" if config.OFFLINE else config.WATSONX_EMBED_MODEL_ID
    print(f"Indexed {len(chunks)} chunks from {len({c['source_id'] for c in chunks})} sources ({mode})")


if __name__ == "__main__":
    main()
