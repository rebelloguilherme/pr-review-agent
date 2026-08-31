"""Limite de chamadas simultâneas à OpenRouter.

O paralelismo do grafo (fan-out via `Send`, ver `agent/nodes.py`) continua
real — o LangGraph despacha `analyze_one_file` para vários arquivos ao
mesmo tempo. Este semáforo serializa só as chamadas de rede à OpenRouter
(chat + embeddings), porque a conta usada está no free tier e tem um
orçamento de requisições *in-flight* muito baixo (erro real observado:
`402 in_flight_budget_exhausted` com 2+ chamadas simultâneas). É um
padrão comum em integração com APIs externas com rate limit — separar o
paralelismo da própria aplicação do limite de concorrência do provedor.
"""

import threading

openrouter_semaphore = threading.Semaphore(1)
