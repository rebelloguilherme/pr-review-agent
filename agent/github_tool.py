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


def _raise_if_transient(resp: requests.Response, url: str) -> None:
    """Levanta GitHubTransientError para status transitório (429/5xx) —
    precisa acontecer DENTRO da função decorada com @_retrying() (_get /
    _post), não depois: o tenacity só vê exceções levantadas dentro da
    própria chamada que ele envolve. Um bug real do primeiro rascunho
    (verificação feita em fetch_pr_metadata, fora do retry) foi pego por
    tests/test_github_tool.py::test_fetch_pr_metadata_retries_on_500_then_succeeds."""
    if resp.status_code == 429 or resp.status_code >= 500:
        raise GitHubTransientError(f"GitHub retornou HTTP {resp.status_code} em {url}, tentando de novo.")


@_retrying()
def _get(url: str, token: str, params: dict | None = None) -> requests.Response:
    try:
        resp = requests.get(url, headers=_headers(token), params=params, timeout=REQUEST_TIMEOUT)
    except (requests.Timeout, requests.ConnectionError) as exc:
        raise GitHubTransientError(f"Falha de rede ao chamar {url}: {exc}") from exc
    _raise_if_transient(resp, url)
    return resp


@_retrying()
def _post(url: str, token: str, json_body: dict) -> requests.Response:
    try:
        resp = requests.post(url, headers=_headers(token), json=json_body, timeout=REQUEST_TIMEOUT)
    except (requests.Timeout, requests.ConnectionError) as exc:
        raise GitHubTransientError(f"Falha de rede ao chamar {url}: {exc}") from exc
    _raise_if_transient(resp, url)
    return resp


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
    if not resp.ok:
        raise GitHubAPIError(f"Erro ao buscar PR: HTTP {resp.status_code} - {resp.text[:200]}")
    return resp.json()


def fetch_pr_files(owner: str, repo: str, pr_number: int, token: str) -> list[dict]:
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/files"
    files: list[dict] = []
    page = 1
    while True:
        resp = _get(url, token, params={"per_page": 100, "page": page})
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
    if not resp.ok:
        raise GitHubAPIError(
            f"Erro ao publicar comentário: HTTP {resp.status_code} - {resp.text[:200]}"
        )
    return resp.json().get("html_url", "")
