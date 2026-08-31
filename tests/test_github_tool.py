"""Testes de unidade da tool (agent/github_tool.py), com a API do GitHub
mockada — não fazem chamada de rede real."""

import pytest

from agent.github_tool import (
    GitHubAPIError,
    fetch_pr_files,
    fetch_pr_metadata,
    post_pr_comment,
)


class FakeResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text
        self.ok = 200 <= status_code < 300

    def json(self):
        return self._json


def test_fetch_pr_metadata_success(monkeypatch):
    monkeypatch.setattr(
        "agent.github_tool.requests.get",
        lambda *a, **k: FakeResponse(200, {"title": "Fix bug", "user": {"login": "alice"}}),
    )
    data = fetch_pr_metadata("acme", "demo", 1, "fake-token")
    assert data["title"] == "Fix bug"


def test_fetch_pr_metadata_404(monkeypatch):
    monkeypatch.setattr(
        "agent.github_tool.requests.get", lambda *a, **k: FakeResponse(404, text="not found")
    )
    with pytest.raises(GitHubAPIError, match="não encontrado"):
        fetch_pr_metadata("acme", "demo", 999, "fake-token")


def test_fetch_pr_metadata_unauthorized(monkeypatch):
    monkeypatch.setattr(
        "agent.github_tool.requests.get", lambda *a, **k: FakeResponse(401, text="bad token")
    )
    with pytest.raises(GitHubAPIError, match="inválido"):
        fetch_pr_metadata("acme", "demo", 1, "bad-token")


def test_fetch_pr_metadata_retries_on_500_then_succeeds(monkeypatch):
    calls = {"n": 0}

    def fake_get(*a, **k):
        calls["n"] += 1
        if calls["n"] < 3:
            return FakeResponse(500, text="server error")
        return FakeResponse(200, {"title": "ok after retry"})

    monkeypatch.setattr("agent.github_tool.requests.get", fake_get)
    data = fetch_pr_metadata("acme", "demo", 1, "fake-token")
    assert data["title"] == "ok after retry"
    assert calls["n"] == 3


def test_fetch_pr_files_paginates(monkeypatch):
    pages = [
        [{"filename": f"file{i}.py"} for i in range(100)],
        [{"filename": "last.py"}],
    ]

    def fake_get(url, headers, params, timeout):
        page = params["page"]
        return FakeResponse(200, pages[page - 1])

    monkeypatch.setattr("agent.github_tool.requests.get", fake_get)
    files = fetch_pr_files("acme", "demo", 1, "fake-token")
    assert len(files) == 101
    assert files[-1]["filename"] == "last.py"


def test_post_pr_comment_success(monkeypatch):
    monkeypatch.setattr(
        "agent.github_tool.requests.post",
        lambda *a, **k: FakeResponse(
            201, {"html_url": "https://github.com/acme/demo/pull/1#issuecomment-1"}
        ),
    )
    url = post_pr_comment("acme", "demo", 1, "relatório de teste", "fake-token")
    assert url.endswith("issuecomment-1")


def test_post_pr_comment_error(monkeypatch):
    monkeypatch.setattr(
        "agent.github_tool.requests.post", lambda *a, **k: FakeResponse(422, text="invalid body")
    )
    with pytest.raises(GitHubAPIError, match="Erro ao publicar"):
        post_pr_comment("acme", "demo", 1, "corpo inválido", "fake-token")
