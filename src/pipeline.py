"""Public entry point: check_claim(text) -> Verdict."""
import time

from src import folk, graph, retrieve
from src.config import APP_FLAGS, Flags
from src.judge import judge
from src.schema import Verdict


def check_claim(text: str, flags: Flags = APP_FLAGS) -> Verdict:
    t0 = time.perf_counter()
    if flags.agent:
        v = graph.run(text, flags)
    else:
        tokens, understood, query = 0, "", text
        if flags.folk:
            query, understood, tokens = folk.normalize(text)
        chunks = retrieve.search(query, k=5, hybrid=flags.hybrid)
        v = judge(text, chunks, understood)
        v = v.model_copy(update={"tokens": v.tokens + tokens})
    return v.model_copy(update={"latency_ms": int((time.perf_counter() - t0) * 1000)})
