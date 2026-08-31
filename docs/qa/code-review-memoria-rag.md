# Revisão do PR: feat: RAG (guia de boas praticas) + memoria de execucao

- **Autor:** rebelloguilherme
- **Branch:** `feature/memoria-rag` -> `develop`
- **Arquivos analisados:** 7

## Descrição do PR
## O que muda
- RAG leve sobre docs/guidelines/*.md (chunking por secao, embeddings via OpenRouter, cosseno proprio) injetado no prompt de analise por arquivo.
- Semaforo dedicado (agent/rate_limit.py) para chamadas a OpenRouter, separando o paralelismo do grafo do limite de concorrencia do provedor.
- max_tokens reduzido de 1024 para 512.

## Observacao
A conta de desenvolvimento na OpenRouter esgotou o saldo do free tier durante os testes (documentado no README, secao Limitacoes). A logica de indexacao/recuperacao foi validada isoladamente com embeddings reais antes disso.

Relacionado ao Projeto Avaliativo M2 (evolucao do mini-projeto M1).

## Análise por arquivo
### `README.md`
• **Risco de segurança**: Menção explícita de credenciais e limites de conta (free tier OpenRouter esgotado, saldo de créditos). Documentar detalhes de falhas de autenticação (`402`) pode expor informações sensíveis — considere generalizar ou mover para seção interna.

• **Inconsistência técnica**: Afirma que embeddings são "guardados em memória do processo (sem banco vetorial)" mas não esclarece o ciclo de vida — se o processo reinicia, os embeddings são recalculados? Isso impacta custo e latência; precisa ser explícito.

• **Falta de clareza sobre fallback**: "Se a recuperação falhar... a análise segue sem o contexto" — não fica claro se a qualidade da revisão degrada significativamente ou se é aceitável. Adicione impacto esperado.

• **Boas práticas de documentação**: A seção "Contexto e memória" é densa e técnica; considere adicionar um diagrama ou tabela comparativa das duas camadas para melhor legibilidade.

• **Risco de regressão**: Redução de `max_tokens` de 1024 para 512 "é compatível com o que é pedido (até 5 bullets)" — isso é uma justificativa fraca. Valide se análises reais não ficam truncadas; documente trade-off explicitamente.

### `agent/memory.py`
• **Risco de segurança — variável global mutável sem sincronização completa**: `_embeddings_client` é acessado fora do lock em `_get_embeddings_client()`, permitindo race condition e múltiplas instâncias. Use lock ou `threading.local()`.

• **Bug potencial — divisão por zero não tratada**: em `_cosine_similarity()`, vetores com norma zero retornam 0.0, mas embeddings reais nunca devem ser zero; considere adicionar validação ou log de aviso.

• **Risco de performance — sem cache de embeddings**: cada chamada a `retrieve_relevant_guidelines()` recalcula embedding da query; considere cache com TTL ou memoização para queries repetidas.

• **Boas práticas — exception handling muito genérico**: `except Exception` com `# noqa: BLE001` mascara erros reais (rede, API, auth); capture apenas `Exception` esperadas ou registre o erro para debug.

• **Boas práticas — falta de validação de entrada**: `query` não é validado (vazio, None, muito longo); adicione validação mínima antes de chamar `embed_query()`.

### `agent/nodes.py`
Análise indisponível para este arquivo após novas tentativas (erro: Error code: 402 - {'error': {'message': 'This request would exceed your available credits given your current in-flight requests. Retry after in-flight requests settle, or add credits.', 'code': 402, 'metadata': {'reason': 'in_flight_budget_exhausted', 'limit_source': 'openrouter_in_flight_budget', 'remedy_hint': 'Retry after your in-flight requests settle (see the Retry-After header). Adding credits at https://openrouter.ai/settings/credits raises your in-flight budget, up to a capped ceiling.', 'headers': {'Retry-After': '120'}, 'provider_name': None}}, 'user_id': 'user_3EbQ1KJZoWZa5a9msqFHNWGzvqI'}).

### `agent/rate_limit.py`
Análise indisponível para este arquivo após novas tentativas (erro: Error code: 402 - {'error': {'message': 'This request would exceed your available credits given your current in-flight requests. Retry after in-flight requests settle, or add credits.', 'code': 402, 'metadata': {'reason': 'in_flight_budget_exhausted', 'limit_source': 'openrouter_in_flight_budget', 'remedy_hint': 'Retry after your in-flight requests settle (see the Retry-After header). Adding credits at https://openrouter.ai/settings/credits raises your in-flight budget, up to a capped ceiling.', 'headers': {'Retry-After': '120'}, 'provider_name': None}}, 'user_id': 'user_3EbQ1KJZoWZa5a9msqFHNWGzvqI'}).

### `docs/guidelines/backend-dotnet.md`
Análise indisponível para este arquivo após novas tentativas (erro: Error code: 402 - {'error': {'message': 'This request would exceed your available credits given your current in-flight requests. Retry after in-flight requests settle, or add credits.', 'code': 402, 'metadata': {'reason': 'in_flight_budget_exhausted', 'limit_source': 'openrouter_in_flight_budget', 'remedy_hint': 'Retry after your in-flight requests settle (see the Retry-After header). Adding credits at https://openrouter.ai/settings/credits raises your in-flight budget, up to a capped ceiling.', 'headers': {'Retry-After': '120'}, 'provider_name': None}}, 'user_id': 'user_3EbQ1KJZoWZa5a9msqFHNWGzvqI'}).

### `docs/guidelines/frontend-typescript.md`
Análise indisponível para este arquivo após novas tentativas (erro: Error code: 402 - {'error': {'message': 'This request would exceed your available credits given your current in-flight requests. Retry after in-flight requests settle, or add credits.', 'code': 402, 'metadata': {'reason': 'in_flight_budget_exhausted', 'limit_source': 'openrouter_in_flight_budget', 'remedy_hint': 'Retry after your in-flight requests settle (see the Retry-After header). Adding credits at https://openrouter.ai/settings/credits raises your in-flight budget, up to a capped ceiling.', 'headers': {'Retry-After': '120'}, 'provider_name': None}}, 'user_id': 'user_3EbQ1KJZoWZa5a9msqFHNWGzvqI'}).

### `docs/guidelines/seguranca-geral.md`
Análise indisponível para este arquivo após novas tentativas (erro: Error code: 402 - {'error': {'message': 'This request would exceed your available credits given your current in-flight requests. Retry after in-flight requests settle, or add credits.', 'code': 402, 'metadata': {'reason': 'in_flight_budget_exhausted', 'limit_source': 'openrouter_in_flight_budget', 'remedy_hint': 'Retry after your in-flight requests settle (see the Retry-After header). Adding credits at https://openrouter.ai/settings/credits raises your in-flight budget, up to a capped ceiling.', 'headers': {'Retry-After': '120'}, 'provider_name': None}}, 'user_id': 'user_3EbQ1KJZoWZa5a9msqFHNWGzvqI'}).

## Conclusão
Foram identificados pontos de atenção acima — revisar antes do merge.