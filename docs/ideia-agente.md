# Ideia do agente — pr-review-agent

## Problema

Revisar Pull Requests manualmente é lento e repetitivo: o revisor precisa abrir
cada arquivo alterado, entender o diff, procurar problemas óbvios (bugs,
riscos, más práticas) antes mesmo de avaliar decisões de design. Isso atrasa o
ciclo de revisão e consome tempo de desenvolvedores sênior com tarefas que
poderiam ser triadas automaticamente.

## Objetivo

Revisar automaticamente um Pull Request do GitHub, apontando riscos,
problemas de estilo/boas práticas e um resumo das mudanças — funcionando como
uma primeira passada automatizada antes da revisão humana.

## Entrada

- `owner/repo` (ex: `octocat/Hello-World`)
- Número do PR (ou URL completa do PR, da qual `owner/repo` e número são
  extraídos)

## Processo (LangGraph)

Grafo com estado compartilhado entre os nós (`pr_info`, `files`,
`file_analyses` acumuladas, `report`, `error`):

1. **`fetch_pr`** — chama a GitHub API para validar que o PR existe e é
   acessível com o token configurado; busca metadata (título, descrição,
   autor, base/head) e a lista de arquivos alterados com o diff de cada um.
   Se o PR não existir, o repo for inacessível ou o token for inválido, o
   estado é marcado com `error` e o grafo desvia para o nó de erro.
2. **`analyze_files`** — para cada arquivo alterado, envia o diff ao modelo
   (Claude) pedindo uma análise objetiva: bugs prováveis, riscos de
   segurança/regressão, sugestões de estilo/boas práticas. Os resultados vão
   se acumulando no estado do grafo (contexto/memória da execução).
3. **`generate_report`** — consolida as análises por arquivo em um relatório
   final estruturado.
4. **`handle_error`** — nó alternativo acionado quando a validação em
   `fetch_pr` falha; retorna uma mensagem de erro clara em vez de quebrar a
   execução.

## Saída

Relatório estruturado em Markdown contendo:

- Resumo geral do PR (título, autor, objetivo inferido)
- Lista de arquivos analisados
- Comentários/sugestões por arquivo
- Conclusão geral (ex.: "pronto para merge" / "requer atenção antes do
  merge")

## Ferramenta integrada

GitHub REST API (via `requests`), autenticada com um Personal Access Token
(`GITHUB_TOKEN`) de escopo de leitura, usada para buscar metadata do PR e o
diff de cada arquivo alterado — uma ação real de chamada a API, não simulada.

## Modelo de linguagem

Claude Haiku 4.5 (Anthropic), acessado via [OpenRouter](https://openrouter.ai)
com `langchain-openai` (`ChatOpenAI` apontado para a base URL da OpenRouter),
chamado no nó `analyze_files` para gerar a análise de cada diff. A troca para
OpenRouter foi uma decisão de custo/billing — mesma família de modelo Claude,
cobrança via créditos da OpenRouter em vez da conta Anthropic direta.
