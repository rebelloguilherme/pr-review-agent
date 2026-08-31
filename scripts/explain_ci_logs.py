"""Usa o LLM para explicar, em linguagem natural, o que aconteceu em
etapas reais do pipeline de CI/CD — a partir de logs REAIS baixados do
GitHub Actions (não simulados), capturados em docs/evidencias/ci-logs/
durante uma anomalia real gerada de propósito (ver README).

Uso: python scripts/explain_ci_logs.py
Requer OPENROUTER_API_KEY no .env. Faz só 1 chamada ao LLM (as duas
etapas são explicadas juntas, no mesmo prompt, para economizar custo).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

LOG_DIR = Path(__file__).resolve().parent.parent / "docs" / "evidencias" / "ci-logs"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "docs" / "evidencias" / "explicacao-logs-ci.md"

MAX_CHARS_PER_LOG = 3000

PROMPT = """Você é um engenheiro de DevOps sênior explicando logs de CI/CD para o time.

Abaixo estão trechos REAIS de duas etapas de um pipeline de GitHub Actions do mesmo projeto:

ETAPA 1 — execução que FALHOU (job "test", depois de uma regressão proposital):
```
{failure_log}
```

ETAPA 2 — execução seguinte, já com a regressão revertida (job "test", sucesso):
```
{success_log}
```

Explique em português, de forma objetiva (no máximo 8 bullets no total):
- O que causou a falha na Etapa 1 (nome do teste, causa raiz no código-fonte se identificável pelo nome do teste).
- Por que a Etapa 2 passou.
- Qualquer padrão ou risco que valha a pena monitorar no pipeline a partir disso.
"""


def _read_relevant_excerpt(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    # Foca no trecho do job "test" (nome do job vem no início de cada linha do log baixado por `gh run view --log`)
    lines = [line for line in text.splitlines() if line.startswith("test\t")]
    excerpt = "\n".join(lines) if lines else text
    return excerpt[:MAX_CHARS_PER_LOG]


def main() -> None:
    load_dotenv()
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY não configurado — abortando.", file=sys.stderr)
        sys.exit(1)

    failure_log = _read_relevant_excerpt(LOG_DIR / "run-failure-test-step.log")
    success_log = _read_relevant_excerpt(LOG_DIR / "run-recovery-success-full.log")

    llm = ChatOpenAI(
        model="anthropic/claude-haiku-4.5",
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        temperature=0,
        max_tokens=350,
    )
    response = llm.invoke(PROMPT.format(failure_log=failure_log, success_log=success_log))
    content = response.content if isinstance(response.content, str) else str(response.content)

    OUTPUT_FILE.write_text(
        "# Explicação de logs de CI/CD com IA\n\n"
        "Baseado em execuções reais do pipeline "
        "(`docs/evidencias/ci-logs/run-failure-test-step.log` e "
        "`run-recovery-success-full.log`), geradas a partir de uma "
        "regressão proposital seguida de correção — ver README, seção "
        "QA, observabilidade e DevOps.\n\n" + content + "\n",
        encoding="utf-8",
    )
    print(content)
    print(f"\nSalvo em {OUTPUT_FILE}", file=sys.stderr)


if __name__ == "__main__":
    main()
