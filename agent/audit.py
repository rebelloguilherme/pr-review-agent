"""Trilha de auditoria — sinal de observabilidade nº 2.

Diferente dos logs técnicos (`agent/observability.py`), este arquivo
registra apenas **decisões de governança**: aprovação usada, prompt
injection detectado, comentário publicado/bloqueado. É o registro que
respondería, depois do fato, "quem autorizou isso?" ou "por que essa
ação não aconteceu?" — o tipo de pergunta que um log de performance não
responde bem.

Formato: 1 JSON por linha em `logs/audit.jsonl`, correlacionado pelo
mesmo `trace_id` usado nos logs estruturados e no checkpointer do grafo.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

AUDIT_DIR = Path(__file__).resolve().parent.parent / "logs"
AUDIT_FILE = AUDIT_DIR / "audit.jsonl"


def record_audit_event(trace_id: str, event: str, **fields) -> None:
    AUDIT_DIR.mkdir(exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "event": event,
        **fields,
    }
    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_audit_trail(trace_id: str | None = None) -> list[dict]:
    """Lê a trilha de auditoria (opcionalmente filtrada por trace_id) —
    usado para investigar uma execução específica (ver README)."""
    if not AUDIT_FILE.exists():
        return []
    entries = []
    with AUDIT_FILE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if trace_id is None or entry.get("trace_id") == trace_id:
                entries.append(entry)
    return entries
