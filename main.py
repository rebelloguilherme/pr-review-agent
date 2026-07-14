import argparse
import sys
from urllib.parse import urlparse

from dotenv import load_dotenv

from agent.graph import build_graph


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
    }
    result = graph.invoke(initial_state)
    report = result["report"]
    print(report)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nRelatório salvo em {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
