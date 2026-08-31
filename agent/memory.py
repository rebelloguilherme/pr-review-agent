"""Recuperação de contexto (RAG) sobre um pequeno guia de boas práticas.

Estratégia adotada, documentada aqui e no README:

- Base: arquivos Markdown em `docs/guidelines/` (backend, frontend,
  segurança) — conteúdo curto, mantido no próprio repositório.
- Chunking: cada arquivo é dividido por seção (`## `), sem overlap — as
  seções já são curtas e semanticamente coesas, overlap não agrega aqui.
- Indexação: embeddings via `openai/text-embedding-3-small`, servido pela
  OpenRouter (mesmo provedor já usado para o LLM de análise). Guardados em
  memória do processo (lista de vetores), sem banco vetorial dedicado —
  a base tem poucas dezenas de chunks, não justifica um Chroma/FAISS em
  disco para este escopo. Ver "Decisões tomadas" no README para o
  trade-off.
- Recuperação: similaridade de cosseno pura em Python contra o texto de
  consulta (nome do arquivo + trecho do diff), top-k=2 por análise.
"""

from __future__ import annotations

import math
import os
import threading
from dataclasses import dataclass
from pathlib import Path

from langchain_openai import OpenAIEmbeddings

from .rate_limit import openrouter_semaphore

GUIDELINES_DIR = Path(__file__).resolve().parent.parent / "docs" / "guidelines"
EMBEDDING_MODEL = "openai/text-embedding-3-small"
# Mesma base da OpenRouter usada pelo LLM de análise (agent/nodes.py) —
# duplicado aqui (em vez de importado) para evitar import circular entre
# os dois módulos.
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


@dataclass
class Chunk:
    source: str
    text: str
    embedding: list[float]


_index: list[Chunk] | None = None
_index_lock = threading.Lock()
_embeddings_client: OpenAIEmbeddings | None = None
_embeddings_client_lock = threading.Lock()


def _get_embeddings_client() -> OpenAIEmbeddings:
    """Lazy singleton, protegido por lock: `analyze_one_file` roda em
    paralelo (via Send) e cada branch pode chamar isto quase ao mesmo
    tempo na primeira execução. Sem o lock, duas threads podiam checar
    `_embeddings_client is None` como True simultaneamente e cada uma
    instanciar seu próprio `OpenAIEmbeddings` — não corrompe nada, mas
    desperdiça a criação do client. Achado numa revisão de código com IA
    sobre este mesmo arquivo (ver docs/qa/code-review-memoria-rag.md)."""
    global _embeddings_client
    if _embeddings_client is None:
        with _embeddings_client_lock:
            if _embeddings_client is None:
                _embeddings_client = OpenAIEmbeddings(
                    model=EMBEDDING_MODEL,
                    base_url=OPENROUTER_BASE_URL,
                    api_key=os.environ["OPENROUTER_API_KEY"],
                )
    return _embeddings_client


def _chunk_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    sections = text.split("\n## ")
    chunks = []
    for i, section in enumerate(sections):
        section = section if i == 0 else "## " + section
        section = section.strip()
        if section:
            chunks.append(section)
    return chunks


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def build_index() -> list[Chunk]:
    global _index
    if _index is not None:
        return _index

    with _index_lock:
        if _index is not None:  # outra thread pode ter construído enquanto esperávamos o lock
            return _index

        if not GUIDELINES_DIR.exists():
            _index = []
            return _index

        all_chunks: list[tuple[str, str]] = []
        for md_file in sorted(GUIDELINES_DIR.glob("*.md")):
            for chunk_text in _chunk_file(md_file):
                all_chunks.append((md_file.name, chunk_text))

        if not all_chunks:
            _index = []
            return _index

        with openrouter_semaphore:
            embeddings = _get_embeddings_client().embed_documents([c[1] for c in all_chunks])
        _index = [
            Chunk(source=source, text=text, embedding=emb)
            for (source, text), emb in zip(all_chunks, embeddings)
        ]
        return _index


def retrieve_relevant_guidelines(query: str, k: int = 2) -> list[Chunk]:
    """Retorna os `k` chunks de guideline mais similares à query (por
    cosseno). Falha silenciosamente (lista vazia) se a base ainda não
    existir ou se a chamada de embeddings falhar — a análise do arquivo
    continua sem contexto de guideline em vez de derrubar a execução."""
    index = build_index()
    if not index:
        return []
    try:
        with openrouter_semaphore:
            query_embedding = _get_embeddings_client().embed_query(query)
    except Exception:  # noqa: BLE001 — fallback deliberado: sem guideline não derruba a análise
        return []
    scored = sorted(
        index, key=lambda c: _cosine_similarity(c.embedding, query_embedding), reverse=True
    )
    return scored[:k]
