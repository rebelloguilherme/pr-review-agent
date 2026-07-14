import requests

GITHUB_API_URL = "https://api.github.com"


class GitHubAPIError(Exception):
    pass


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "pr-review-agent",
    }


def fetch_pr_metadata(owner: str, repo: str, pr_number: int, token: str) -> dict:
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
    resp = requests.get(url, headers=_headers(token), timeout=15)
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
        resp = requests.get(
            url, headers=_headers(token), params={"per_page": 100, "page": page}, timeout=15
        )
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
