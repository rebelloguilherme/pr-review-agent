from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .nodes import (
    analyze_one_file,
    fetch_pr,
    generate_report,
    handle_error,
    route_after_fetch,
)
from .state import PRReviewState


def build_graph():
    builder = StateGraph(PRReviewState)
    builder.add_node("fetch_pr", fetch_pr)
    builder.add_node("analyze_one_file", analyze_one_file)
    builder.add_node("generate_report", generate_report)
    builder.add_node("handle_error", handle_error)

    builder.add_edge(START, "fetch_pr")
    # `route_after_fetch` retorna "handle_error" (string, resolvida via
    # path_map) OU uma lista de `Send("analyze_one_file", ...)` — 1 por
    # arquivo do PR, executados em paralelo (fan-out). Como todos os
    # `Send` apontam para o mesmo nó de destino, o LangGraph sincroniza
    # (join) automaticamente antes de seguir para `generate_report`.
    builder.add_conditional_edges(
        "fetch_pr",
        route_after_fetch,
        {"handle_error": "handle_error"},
    )
    builder.add_edge("analyze_one_file", "generate_report")
    builder.add_edge("generate_report", END)
    builder.add_edge("handle_error", END)

    # Checkpointer em memória: permite inspecionar/retomar uma execução por
    # `thread_id` (usamos o número do PR) — ver `docs/memoria.md`.
    return builder.compile(checkpointer=MemorySaver())
