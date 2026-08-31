"""Integração com a automação low-code/no-code (n8n).

Ao final de cada execução, se `N8N_WEBHOOK_URL` estiver configurado, o
agente chama esse webhook com um resumo do resultado. O fluxo n8n (ver
`low-code/workflow.json` e README, seção "Automação low-code/no-code")
recebe esse gatilho e formata/envia uma notificação para o Discord.

A lógica de revisão em si continua 100% na aplicação — o n8n só atua
como orquestração/notificação de saída, exatamente como pedido pelo
edital ("a lógica principal deverá permanecer na aplicação, enquanto a
ferramenta visual deverá atuar como apoio à orquestração ou integração").

Best-effort e não bloqueante: uma falha aqui é só logada, nunca derruba a
execução principal (a revisão do PR já terminou nesse ponto).
"""

from __future__ import annotations

import os

import requests

from .observability import get_logger

WEBHOOK_TIMEOUT = 5


def notify_low_code(trace_id: str, payload: dict) -> None:
    log = get_logger(trace_id)
    url = os.environ.get("N8N_WEBHOOK_URL")
    if not url:
        log.info("low_code.skipped", reason="N8N_WEBHOOK_URL não configurado")
        return
    try:
        requests.post(url, json=payload, timeout=WEBHOOK_TIMEOUT)
        log.info("low_code.notified", url=url)
    except Exception as exc:  # noqa: BLE001 — best-effort: notificação nunca derruba a execução
        log.warning("low_code.failed", error=str(exc))
