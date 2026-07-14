from typing import Optional, TypedDict


class FileChange(TypedDict):
    filename: str
    status: str
    additions: int
    deletions: int
    patch: Optional[str]


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
    pr_info: Optional[PRInfo]
    files: list[FileChange]
    file_analyses: list[FileAnalysis]
    report: Optional[str]
    error: Optional[str]
