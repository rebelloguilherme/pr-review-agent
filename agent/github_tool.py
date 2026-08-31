import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

GITHUB_API_URL = "https://api.github.com"
REQUEST_TIMEOUT = 15


class GitHubAPIError(Exception):
    pass


class GitHubTransientError(GitHubAPIError):
    """Erro de rede/timeout — vale a pena tentar de novo (retry)."""


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "pr-review-agent",
    }


def _retrying():
    return retry(
        retry=retry_if_exception_type(GitHubTransientError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )


@_retrying()
def _get(url: str, token: str, params: dict | None = None) -> requests.Response:
    try:
        return requests.get(url, headers=_headers(token), params=params, timeout=REQUEST_TIMEOUT)
    except (requests.Timeout, requests.ConnectionError) as exc:
        raise GitHubTransientError(f"Falha de rede ao chamar {url}: {exc}") from exc


@_retrying()
def _post(url: str, token: str, json_body: dict) -> requests.Response:
    try:
        return requests.post(url, headers=_headers(token), json=json_body, timeout=REQUEST_TIMEOUT)
    except (requests.Timeout, requests.ConnectionError) as exc:
        raise GitHubTransientError(f"Falha de rede ao chamar {url}: {exc}") from exc


def fetch_pr_metadata(owner: str, repo: str, pr_number: int, token: str) -> dict:
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
    resp = _get(url, token)
    if resp.status_code == 404:
        raise GitHubAPIError(
            f"PR #{pr_number} não encontrado em {owner}/{repo} "
            "(ou o token não tem acesso a este repositório)."
        )
    if resp.status_code in (401, 403):
        raise GitHubAPIError("Token do GitHub inválido ou sem permissão para este repositório.")
    if resp.status_code == 429 or resp.status_code >= 500:
        raise GitHubTransientError(f"GitHub retornou HTTP {resp.status_code}, tentando de novo.")
    if not resp.ok:
        raise GitHubAPIError(f"Erro ao buscar PR: HTTP {resp.status_code} - {resp.text[:200]}")
    return resp.json()


def fetch_pr_files(owner: str, repo: str, pr_number: int, token: str) -> list[dict]:
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/files"
    files: list[dict] = []
    page = 1
    while True:
        resp = _get(url, token, params={"per_page": 100, "page": page})
        if resp.status_code == 429 or resp.status_code >= 500:
            raise GitHubTransientError(f"GitHub retornou HTTP {resp.status_code}, tentando de novo.")
        if not resp.ok:
            raise GitHubAPIError(
                f"Erro ao buscar arquivos do PR: HTTP {resp.status_code} - {resp.text[:200]}"
            )
        batch = resp.json()
        if not batch:
            break
        files.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return files


def post_pr_comment(owner: str, repo: str, pr_number: int, body: str, token: str) -> str:
    """Publica um comentário no PR. Ação real, pública e não trivial de
    desfazer — só deve ser chamada depois dos guardrails de governança
    (ver `agent/nodes.py::post_comment`), nunca diretamente a partir de
    uma decisão do LLM."""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{pr_number}/comments"
    resp = _post(url, token, {"body": body})
    if resp.status_code == 429 or resp.status_code >= 500:
        raise GitHubTransientError(f"GitHub retornou HTTP {resp.status_code}, tentando de novo.")
    if not resp.ok:
        raise GitHubAPIError(
            f"Erro ao publicar comentário: HTTP {resp.status_code} - {resp.text[:200]}"
        )
    return resp.json().get("html_url", "")
