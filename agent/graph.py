from langgraph.graph import END, START, StateGraph

from .nodes import analyze_files, fetch_pr, generate_report, handle_error, route_after_fetch
from .state import PRReviewState


def build_graph():
    builder = StateGraph(PRReviewState)
    builder.add_node("fetch_pr", fetch_pr)
    builder.add_node("analyze_files", analyze_files)
    builder.add_node("generate_report", generate_report)
    builder.add_node("handle_error", handle_error)

    builder.add_edge(START, "fetch_pr")
    builder.add_conditional_edges(
        "fetch_pr",
        route_after_fetch,
        {"analyze_files": "analyze_files", "handle_error": "handle_error"},
    )
    builder.add_edge("analyze_files", "generate_report")
    builder.add_edge("generate_report", END)
    builder.add_edge("handle_error", END)

    return builder.compile()
