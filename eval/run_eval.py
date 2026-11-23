"""Evaluate a pipeline variant on data/eval_claims.jsonl and append a row to eval/ablation.md.

Usage: python -m eval.run_eval --variant baseline
       python -m eval.run_eval --variant hybrid+folk --flags hybrid,folk
"""
import argparse
import json
import statistics
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src import config
from src.config import Flags
from src.pipeline import check_claim

OUT = Path(__file__).resolve().parent
HEADER = "| Variant | Mode | Claims | Accuracy | Recall@5 | p50 latency (ms) | Avg tokens | Cost/request |\n|---|---|---|---|---|---|---|---|\n"


def load_claims(limit: int | None) -> list[dict]:
    available = {p.stem for p in config.SOURCES_DIR.glob("*.md")}
    rows = [json.loads(l) for l in config.CLAIMS_PATH.read_text("utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r["gold_source"] in available]
    return rows[:limit] if limit else rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True)
    ap.add_argument("--flags", default="")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    flags = Flags.parse(args.flags)
    claims = load_claims(args.limit)
    if not claims:
        raise SystemExit("No claims whose gold_source exists in data/sources/")

    def run(c: dict) -> dict:
        v = check_claim(c["claim"], flags)
        top = [ch.source_id for ch in v.retrieved[:5]]
        return {"id": c["id"], "claim": c["claim"], "gold": c["label"], "pred": v.label,
                "correct": v.label == c["label"], "recall": c["gold_source"] in top,
                "latency_ms": v.latency_ms, "tokens": v.tokens, "understood": v.understood,
                "retried": bool(v.retried_query)}

    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(run, claims))

    n = len(results)
    acc = sum(r["correct"] for r in results) / n
    rec = sum(r["recall"] for r in results) / n
    p50 = statistics.median(r["latency_ms"] for r in results)
    tok = sum(r["tokens"] for r in results) / n
    cost = tok / 1000 * config.PRICE_PER_1K_TOKENS
    mode = "offline" if config.OFFLINE else config.WATSONX_MODEL_ID

    (OUT / "results").mkdir(exist_ok=True)
    (OUT / "results" / f"{args.variant}.json").write_text(
        json.dumps({"variant": args.variant, "flags": args.flags, "results": results}, ensure_ascii=False, indent=2), "utf-8")
    table = OUT / "ablation.md"
    if not table.exists():
        table.write_text(HEADER, "utf-8")
    with table.open("a", encoding="utf-8") as f:
        f.write(f"| {args.variant} | {mode} | {n} | {acc:.0%} | {rec:.0%} | {p50:.0f} | {tok:.0f} | ${cost:.5f} |\n")

    print(f"{args.variant}: accuracy {acc:.0%}, recall@5 {rec:.0%}, p50 {p50:.0f} ms, tokens {tok:.0f}, n={n}")
    for r in results:
        if not r["correct"]:
            print(f"  wrong #{r['id']}: gold={r['gold']} pred={r['pred']} | {r['claim']}")


if __name__ == "__main__":
    main()
