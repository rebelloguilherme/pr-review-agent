"""Logs estruturados (JSON) — sinal de observabilidade nº 1.

Cada execução do agente usa `trace_id = "{owner}/{repo}#{pr_number}"` — o
mesmo identificador já usado como `thread_id` do checkpointer do grafo
(ver `agent/graph.py`), de propósito: um único identificador correlaciona
o estado retomável da execução (LangGraph), os logs técnicos (aqui) e a
trilha de auditoria (`agent/audit.py`, sinal nº 2). Ver
"Observabilidade e resiliência" no README para como os dois sinais são
usados juntos para investigar uma execução real.

Este arquivo cobre o lado "operacional": início/fim de cada nó, latência,
erros e retries — pensado para debugar performance e falhas. A trilha de
auditoria cobre o lado "governança": quem decidiu o quê e por quê.
"""

from __future__ import annotations

import sys
from pathlib import Path

import structlog

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "agent.jsonl"

_configured = False


def configure_logging() -> None:
    """Configura o structlog para escrever 1 JSON por linha em
    logs/agent.jsonl (append). Chamado de forma idempotente — pode ser
    invocado várias vezes (cada nó do grafo chama get_logger()) sem
    reconfigurar ou reabrir o arquivo mais de uma vez."""
    global _configured
    if _configured:
        return
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_FILE.open("a", encoding="utf-8")

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=log_file),
        cache_logger_on_first_use=True,
    )
    _configured = True


def get_logger(trace_id: str | None = None) -> structlog.stdlib.BoundLogger:
    configure_logging()
    logger = structlog.get_logger("pr-review-agent")
    if trace_id:
        logger = logger.bind(trace_id=trace_id)
    return logger


def echo_to_stderr(message: str) -> None:
    """Além do arquivo JSON, ecoa uma linha legível no console — útil para
    acompanhar a execução ao vivo sem precisar abrir logs/agent.jsonl."""
    print(message, file=sys.stderr)
