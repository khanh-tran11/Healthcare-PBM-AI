"""Goal-based agent (LangGraph): normalize -> retrieve -> judge -> check (retry once or stop).
Falls back to the same loop in plain Python if langgraph is not installed."""
from typing import Optional, TypedDict

from src import folk, retrieve
from src.config import Flags
from src.judge import judge
from src.schema import Chunk, Verdict


class State(TypedDict, total=False):
    claim: str
    flags: Flags
    query: str
    understood: str
    tokens: int
    chunks: list[Chunk]
    verdict: Optional[Verdict]
    retried_query: Optional[str]


def n_normalize(s: State) -> State:
    if s["flags"].folk:
        q, u, t = folk.normalize(s["claim"])
        return {"query": q, "understood": u, "tokens": s.get("tokens", 0) + t}
    return {"query": s["claim"], "understood": ""}


def n_retrieve(s: State) -> State:
    return {"chunks": retrieve.search(s["query"], k=5, hybrid=s["flags"].hybrid)}


def n_judge(s: State) -> State:
    v = judge(s["claim"], s["chunks"], s.get("understood", ""))
    return {"verdict": v, "tokens": s.get("tokens", 0) + v.tokens}


def needs_retry(s: State) -> bool:
    v = s["verdict"]
    weak = v.label == "chua_du_bang_chung" or v.confidence < 0.5
    return weak and not s.get("retried_query")


def n_expand(s: State) -> State:
    terms = " ".join(b for _, b in folk.match_terms(s["claim"]))
    q = f"{s['claim']} {terms} {s.get('understood', '')}".strip()
    return {"query": q, "retried_query": q}


def _build():
    from langgraph.graph import END, StateGraph

    g = StateGraph(State)
    g.add_node("normalize", n_normalize)
    g.add_node("retrieve", n_retrieve)
    g.add_node("judge", n_judge)
    g.add_node("expand", n_expand)
    g.set_entry_point("normalize")
    g.add_edge("normalize", "retrieve")
    g.add_edge("retrieve", "judge")
    g.add_conditional_edges("judge", lambda s: "expand" if needs_retry(s) else END)
    g.add_edge("expand", "retrieve")
    return g.compile()


_app = None


def run(claim: str, flags: Flags) -> Verdict:
    global _app
    state: State = {"claim": claim, "flags": flags, "tokens": 0}
    try:
        if _app is None:
            _app = _build()
        state = _app.invoke(state)
    except ImportError:
        for fn in (n_normalize, n_retrieve, n_judge):
            state.update(fn(state))
        if needs_retry(state):
            for fn in (n_expand, n_retrieve, n_judge):
                state.update(fn(state))
    v = state["verdict"]
    return v.model_copy(update={"tokens": state.get("tokens", 0), "retried_query": state.get("retried_query")})
