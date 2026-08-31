"""Guardrails de segurança: detecção de prompt injection e redação de segredos.

Contexto: a descrição do PR e o diff de cada arquivo são **conteúdo
externo não confiável** — vêm de quem abriu o PR, não do operador do
agente — e são enviados ao LLM como parte do prompt de análise. Nada
nesse conteúdo deve ser capaz de mudar o comportamento da aplicação.

Duas camadas, propositalmente independentes uma da outra:

1. **Detecção determinística** (`detect_prompt_injection`) — checagem por
   padrões, feita em código comum, sem depender do LLM "decidir" ignorar
   a instrução maliciosa. É esta camada que efetivamente bloqueia a ação
   de escrita (`post_comment`, ver `agent/nodes.py`) — nunca o texto que o
   modelo devolve.
2. **Redação de segredos** (`redact_secrets`) — defesa em profundidade:
   mesmo que os segredos nunca sejam incluídos no prompt, qualquer saída
   do LLM é varrida antes de virar relatório, para o caso de o modelo
   "alucinar" ou ecoar algo parecido com um valor sensível.

Limitação conhecida (documentada no README): é uma lista de padrões, não
um classificador — cobre os vetores de ataque mais comuns em texto livre
("ignore as instruções anteriores", pedidos de exfiltração de segredo,
jailbreak), mas não é uma defesa completa contra qualquer variação.
"""

import os
import re

_INJECTION_PATTERNS = [
    re.compile(
        r"(ignore|disregard)\s+(all\s+|every\s+|previous\s+|prior\s+|above\s+)*instructions\b",
        re.IGNORECASE,
    ),
    re.compile(r"ignore\s+(todas\s+)?as\s+instruções", re.IGNORECASE),
    re.compile(r"desconsidere\s+(todas\s+)?as\s+instruções", re.IGNORECASE),
    re.compile(r"system\s*prompt", re.IGNORECASE),
    re.compile(r"reveal\s+(the\s+|your\s+)?(api[\s_-]?key|token|secret|password)", re.IGNORECASE),
    re.compile(r"print\s+(the\s+|your\s+)?(api[\s_-]?key|token|secret|env)", re.IGNORECASE),
    re.compile(r"revele?\s+(o\s+|a\s+)?(token|senha|chave|segredo)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a|an)\b", re.IGNORECASE),
    re.compile(r"act\s+as\s+(an?\s+)?(unrestricted|jailbroken|dan)\b", re.IGNORECASE),
]

_SECRET_ENV_VARS = ["GITHUB_TOKEN", "OPENROUTER_API_KEY"]


def detect_prompt_injection(text: str | None) -> bool:
    if not text:
        return False
    return any(pattern.search(text) for pattern in _INJECTION_PATTERNS)


def redact_secrets(text: str) -> str:
    if not text:
        return text
    for var in _SECRET_ENV_VARS:
        value = os.environ.get(var)
        if value and value in text:
            text = text.replace(value, f"[REDACTED:{var}]")
    return text
