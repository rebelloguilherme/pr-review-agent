import os

from langchain_openai import ChatOpenAI
from langgraph.types import Send
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .github_tool import GitHubAPIError, fetch_pr_files, fetch_pr_metadata
from .memory import retrieve_relevant_guidelines
from .rate_limit import openrouter_semaphore
from .state import FileAnalysisInput, PRReviewState

MAX_PATCH_CHARS = 6000
MAX_FILES = 25

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "anthropic/claude-haiku-4.5"

_ANALYSIS_PROMPT = """Você é um revisor de código sênior. Analise o diff abaixo do \
arquivo "{filename}" e aponte, de forma objetiva e curta (até 5 bullets):
- bugs prováveis
- riscos (segurança, regressão, performance)
- sugestões de estilo/boas práticas

Se não houver nada relevante, responda apenas "Sem observações relevantes.".
{guidelines_block}
Diff:
```
{patch}
```"""

_GUIDELINES_BLOCK_TEMPLATE = """
Trechos do guia de boas práticas do time, relevantes para este arquivo \
(use como referência, mas não repita literalmente — aplique ao avaliar o diff):
{guidelines}
"""


def fetch_pr(state: PRReviewState) -> dict:
    owner, repo, pr_number = state["owner"], state["repo"], state["pr_number"]
    if not owner or not repo or not pr_number:
        return {"error": "Entrada inválida: informe owner, repo e número do PR."}

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return {"error": "GITHUB_TOKEN não configurado no .env."}
    if not os.environ.get("OPENROUTER_API_KEY"):
        return {"error": "OPENROUTER_API_KEY não configurado no .env."}

    try:
        pr_data = fetch_pr_metadata(owner, repo, pr_number, token)
        files_data = fetch_pr_files(owner, repo, pr_number, token)
    except GitHubAPIError as exc:
        return {"error": str(exc)}

    pr_info = {
        "title": pr_data.get("title", ""),
        "author": pr_data.get("user", {}).get("login", "desconhecido"),
        "description": (pr_data.get("body") or "").strip(),
        "base": pr_data.get("base", {}).get("ref", ""),
        "head": pr_data.get("head", {}).get("ref", ""),
        "state": pr_data.get("state", ""),
    }
    files = [
        {
            "filename": f.get("filename"),
            "status": f.get("status"),
            "additions": f.get("additions", 0),
            "deletions": f.get("deletions", 0),
            "patch": f.get("patch"),
        }
        for f in files_data
    ]
    return {"pr_info": pr_info, "files": files}


def route_after_fetch(state: PRReviewState) -> str | list[Send]:
    """Aresta condicional: erro -> handle_error; sucesso -> fan-out paralelo.

    Em vez de um único nó que itera os arquivos sequencialmente, despachamos
    um `Send("analyze_one_file", ...)` por arquivo (até MAX_FILES). O
    LangGraph executa essas invocações em paralelo (mesmo "superstep") e só
    segue para o próximo nó ligado a `analyze_one_file` (generate_report)
    quando todas terminarem — é a paralelização real exigida pelo grafo,
    não uma paralelização escondida dentro de um `for`/`asyncio.gather`.
    """
    if state.get("error"):
        return "handle_error"

    files = state["files"][:MAX_FILES]
    if not files:
        return "handle_error"

    return [
        Send("analyze_one_file", {"filename": f["filename"], "patch": f.get("patch")})
        for f in files
    ]


_llm = None


def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=OPENROUTER_MODEL,
            base_url=OPENROUTER_BASE_URL,
            api_key=os.environ["OPENROUTER_API_KEY"],
            temperature=0,
            max_tokens=512,
        )
    return _llm


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=15),
    reraise=True,
)
def _invoke_llm_with_retry(prompt: str) -> str:
    with openrouter_semaphore:
        response = _get_llm().invoke(prompt)
    return response.content if isinstance(response.content, str) else str(response.content)


def analyze_one_file(state: FileAnalysisInput) -> dict:
    """Analisa 1 único arquivo. Executado em paralelo, 1x por arquivo do PR
    (despachado via `Send` em `route_after_fetch`)."""
    filename, patch = state["filename"], state.get("patch")
    if not patch:
        return {
            "file_analyses": [
                {
                    "filename": filename,
                    "analysis": "Sem diff textual disponível (arquivo binário ou muito grande).",
                }
            ]
        }
    guidelines_block = ""
    relevant = retrieve_relevant_guidelines(f"{filename}\n{patch[:1000]}", k=2)
    if relevant:
        formatted = "\n".join(f"- ({c.source}) {c.text[:500]}" for c in relevant)
        guidelines_block = _GUIDELINES_BLOCK_TEMPLATE.format(guidelines=formatted)

    prompt = _ANALYSIS_PROMPT.format(
        filename=filename, patch=patch[:MAX_PATCH_CHARS], guidelines_block=guidelines_block
    )
    try:
        content = _invoke_llm_with_retry(prompt)
    except Exception as exc:  # noqa: BLE001 — fallback deliberado: 1 falha não derruba o PR inteiro
        content = f"Análise indisponível para este arquivo após novas tentativas (erro: {exc})."
    return {"file_analyses": [{"filename": filename, "analysis": content}]}


def generate_report(state: PRReviewState) -> dict:
    pr_info = state["pr_info"]
    lines = [
        f"# Revisão do PR: {pr_info['title']}",
        "",
        f"- **Autor:** {pr_info['author']}",
        f"- **Branch:** `{pr_info['head']}` -> `{pr_info['base']}`",
        f"- **Arquivos analisados:** {len(state['file_analyses'])}",
        "",
    ]
    if pr_info["description"]:
        lines += ["## Descrição do PR", pr_info["description"], ""]

    lines.append("## Análise por arquivo")
    for item in state["file_analyses"]:
        lines += [f"### `{item['filename']}`", item["analysis"], ""]

    lines += ["## Conclusão", _conclude(state["file_analyses"])]
    return {"report": "\n".join(lines)}


def _conclude(analyses: list[dict]) -> str:
    if analyses and all(
        "sem observações relevantes" in a["analysis"].lower() for a in analyses
    ):
        return "Nenhum problema relevante identificado. PR parece pronto para revisão humana final."
    return "Foram identificados pontos de atenção acima — revisar antes do merge."


def handle_error(state: PRReviewState) -> dict:
    return {"report": f"# Erro ao revisar PR\n\n{state['error']}"}
