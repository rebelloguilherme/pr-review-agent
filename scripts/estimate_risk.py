"""Estimativa simples de tendência de risco de falha, a partir de dados
REAIS de execuções passadas do agente (relatórios em docs/evidencias/).

Cada relatório de revisão de PR tem duas informações que usamos como
sinal: "Arquivos analisados: N" (total) e quantas análises viraram
"Análise indisponível..." (fallback do LLM/rede, ver
agent/nodes.py::analyze_one_file). A proporção fallback/total é um proxy
simples de quão saudável a integração com o provedor de LLM está numa
execução específica.

Isto não é uma técnica sofisticada de séries temporais — é uma heurística
deliberadamente simples, documentada como tal (ver README, seção QA,
observabilidade e DevOps), suficiente para o escopo pedido.

Uso: python scripts/estimate_risk.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

EVIDENCE_DIR = Path(__file__).resolve().parent.parent / "docs" / "evidencias"

# Ordem cronológica real dos relatórios (pela ordem em que foram gerados
# durante o desenvolvimento do M2 — ver histórico de commits).
CHRONOLOGICAL_ORDER = [
    "pr1-paralelo-com-fallback.md",
    "pr1-paralelo-execucao-limpa.md",
    "pr3-observabilidade-com-falso-positivo.md",
]


@dataclass
class RunStats:
    name: str
    total_files: int
    fallbacks: int

    @property
    def fallback_rate(self) -> float:
        return self.fallbacks / self.total_files if self.total_files else 0.0


def parse_report(path: Path) -> RunStats | None:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"Arquivos analisados:\*\*\s*(\d+)", text)
    if not match:
        return None
    total = int(match.group(1))
    fallbacks = text.count("Análise indisponível")
    return RunStats(name=path.name, total_files=total, fallbacks=fallbacks)


def classify_trend(rates: list[float]) -> str:
    if len(rates) < 2:
        return "dados insuficientes"
    first_half = rates[: len(rates) // 2] or [rates[0]]
    second_half = rates[len(rates) // 2 :]
    avg_first = sum(first_half) / len(first_half)
    avg_second = sum(second_half) / len(second_half)
    if avg_second > avg_first * 1.3:
        return "CRESCENTE — risco de falha aumentando entre execuções"
    if avg_second < avg_first * 0.7:
        return "DECRESCENTE — risco de falha diminuindo entre execuções"
    return "ESTÁVEL"


def main() -> None:
    runs = []
    for filename in CHRONOLOGICAL_ORDER:
        path = EVIDENCE_DIR / filename
        if not path.exists():
            continue
        stats = parse_report(path)
        if stats:
            runs.append(stats)

    print("Execução                                        | Arquivos | Fallbacks | Taxa")
    print("-" * 85)
    rates = []
    for r in runs:
        rates.append(r.fallback_rate)
        print(f"{r.name:<48} | {r.total_files:>8} | {r.fallbacks:>9} | {r.fallback_rate:>5.0%}")

    trend = classify_trend(rates)
    print()
    print(f"Tendência (1ª metade das execuções vs. 2ª metade): {trend}")
    if rates and rates[-1] > 0.5:
        print(
            "Risco ATUAL: ALTO — mais da metade das análises da execução mais recente "
            "caíram em fallback. Causa raiz identificada: saldo esgotado do free tier "
            "da OpenRouter (ver README, 'Limitações')."
        )


if __name__ == "__main__":
    main()
