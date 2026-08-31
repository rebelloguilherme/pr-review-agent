import operator
from typing import Annotated, TypedDict


class FileChange(TypedDict):
    filename: str
    status: str
    additions: int
    deletions: int
    patch: str | None


class FileAnalysis(TypedDict):
    filename: str
    analysis: str


class PRInfo(TypedDict):
    title: str
    author: str
    description: str
    base: str
    head: str
    state: str


class PRReviewState(TypedDict):
    owner: str
    repo: str
    pr_number: int
    pr_info: PRInfo | None
    files: list[FileChange]
    # Annotated com operator.add: cada branch paralela de analyze_one_file
    # devolve uma lista de 1 item; LangGraph concatena (reduce) os retornos
    # das execuções paralelas em vez de sobrescrever o campo.
    file_analyses: Annotated[list[FileAnalysis], operator.add]
    report: str | None
    error: str | None

    # --- Governança (ver agent/nodes.py::post_comment) ---
    # Entrada: aprovação humana explícita (flag --approve da CLI) para a
    # única ação de escrita do agente (publicar comentário no PR).
    approved: bool
    # Annotated com operator.or_: fetch_pr checa a descrição do PR e cada
    # analyze_one_file checa o próprio diff; uma vez True, permanece True
    # pelo resto da execução (ver agent/security.py).
    injection_detected: Annotated[bool, operator.or_]
    comment_posted: bool
    comment_url: str | None
    governance_note: str | None


class FileAnalysisInput(TypedDict):
    """Estado de entrada de cada execução paralela de `analyze_one_file`.

    É um subconjunto de `PRReviewState` — cada `Send` despacha uma cópia
    disto (um arquivo por vez) em paralelo.
    """

    filename: str
    patch: str | None
