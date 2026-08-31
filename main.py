import argparse
import sys
from urllib.parse import urlparse

from dotenv import load_dotenv

from agent.graph import build_graph

MAX_CONCURRENCY = 2


def parse_pr_ref(ref: str, number: str | None) -> tuple[str, str, int]:
    if ref.startswith("http"):
        parts = urlparse(ref).path.strip("/").split("/")
        if len(parts) >= 4 and parts[2] == "pull":
            return parts[0], parts[1], int(parts[3])
        raise ValueError("URL de PR inválida. Formato esperado: https://github.com/owner/repo/pull/N")

    if "/" in ref and number:
        owner, repo = ref.split("/", 1)
        return owner, repo, int(number)

    raise ValueError(
        "Uso: python main.py <owner/repo> <numero_pr>  ou  python main.py <url_do_pr>"
    )


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Agente de revisão de Pull Requests do GitHub")
    parser.add_argument("pr", help="owner/repo ou URL completa do PR")
    parser.add_argument("number", nargs="?", help="Número do PR (se não usar URL)")
    parser.add_argument("--output", "-o", help="Arquivo para salvar o relatório em Markdown")
    parser.add_argument(
        "--approve",
        action="store_true",
        help=(
            "Aprova a publicação do relatório como comentário no PR (ação real, "
            "pública). Sem esta flag, o agente roda em modo dry-run: gera o "
            "relatório mas não publica nada."
        ),
    )
    args = parser.parse_args()

    try:
        owner, repo, pr_number = parse_pr_ref(args.pr, args.number)
    except ValueError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)

    graph = build_graph()
    initial_state = {
        "owner": owner,
        "repo": repo,
        "pr_number": pr_number,
        "pr_info": None,
        "files": [],
        "file_analyses": [],
        "report": None,
        "error": None,
        "approved": args.approve,
        "injection_detected": False,
        "comment_posted": False,
        "comment_url": None,
        "governance_note": None,
    }
    # thread_id = número do PR: cada PR analisado vira uma "sessão"
    # separada no checkpointer, permitindo inspecionar/retomar a execução.
    # max_concurrency limita quantos nós `analyze_one_file` rodam ao mesmo
    # tempo — sem isso, um PR com muitos arquivos dispara 1 chamada LLM
    # simultânea por arquivo e pode estourar limites de rate/orçamento do
    # provedor (visto na prática: erro 402 "in_flight_budget_exhausted" da
    # OpenRouter ao testar contra um PR com 23 arquivos).
    config = {
        "configurable": {"thread_id": f"{owner}/{repo}#{pr_number}"},
        "max_concurrency": MAX_CONCURRENCY,
    }
    result = graph.invoke(initial_state, config=config)
    report = result["report"]
    print(report)

    if result.get("governance_note"):
        print(f"\n[governança] {result['governance_note']}", file=sys.stderr)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nRelatório salvo em {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
