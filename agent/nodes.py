import os

from langchain_openai import ChatOpenAI

from .github_tool import GitHubAPIError, fetch_pr_files, fetch_pr_metadata
from .state import PRReviewState

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

Diff:
```
{patch}
```"""


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


def route_after_fetch(state: PRReviewState) -> str:
    return "handle_error" if state.get("error") else "analyze_files"


def analyze_files(state: PRReviewState) -> dict:
    llm = ChatOpenAI(
        model=OPENROUTER_MODEL,
        base_url=OPENROUTER_BASE_URL,
        api_key=os.environ["OPENROUTER_API_KEY"],
        temperature=0,
        max_tokens=1024,
    )
    analyses = []
    for f in state["files"][:MAX_FILES]:
        patch = f.get("patch")
        if not patch:
            analyses.append(
                {
                    "filename": f["filename"],
                    "analysis": "Sem diff textual disponível (arquivo binário ou muito grande).",
                }
            )
            continue
        prompt = _ANALYSIS_PROMPT.format(
            filename=f["filename"], patch=patch[:MAX_PATCH_CHARS]
        )
        response = llm.invoke(prompt)
        content = response.content if isinstance(response.content, str) else str(response.content)
        analyses.append({"filename": f["filename"], "analysis": content})
    return {"file_analyses": analyses}


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
