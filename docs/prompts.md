# Prompts usados no desenvolvimento

Este projeto foi planejado e implementado com apoio de um assistente de IA
(Claude Code). Abaixo estão os prompts principais usados em cada etapa —
tanto os que direcionaram o assistente durante o desenvolvimento quanto o
prompt operacional que o próprio agente usa em tempo de execução.

## 1. Planejamento

Prompt inicial que definiu o plano geral do projeto (fases, checklist,
ferramenta escolhida) e depois o kickoff da implementação:

> "Preciso realizar o trabalho [Mini-Projeto Avaliativo]. Já foi definido um
> plano para realizá-lo e para entregar. Vamos iniciar a implementação. me
> ajude, vamos fazer o passo a passo, 1 passo de cada vez."

Combinado com um guardrail explícito, aplicado em toda a sessão:

> "Em caso de dúvida ou possível ambiguidade questione antes de qualquer
> alteração."

Esse guardrail gerou várias perguntas de confirmação ao longo do projeto
(nome do repositório, visibilidade, provedor de LLM, formato dos slides,
modelo a usar) antes de qualquer ação irreversível.

## 2. Definição da ideia do agente (Fase 1)

Para transformar o plano em uma descrição concreta de objetivo/entrada/
processo/saída, o prompt de trabalho foi essencialmente:

> "Descreva o objetivo (revisar PR automaticamente), entrada (link/número do
> PR + repo), processo (buscar diff, analisar mudanças, gerar comentários) e
> saída (relatório estruturado); depois monte os 2 slides pedidos."

O rascunho gerado (objetivo, entrada, processo em 4 passos, saída) foi
validado com o usuário antes de virar `docs/ideia-agente.md` e os slides.

## 3. Implementação do grafo LangGraph (Fase 2)

Sequência de prompts que guiaram a implementação:

1. **Tutorial rápido de LangGraph** — pedido para validar os conceitos de
   estado/nós/conexões com um exemplo mínimo antes de partir para o agente
   real, confirmando a API do LangGraph 1.2.9 instalado.
2. **Estrutura do projeto** — pergunta direta ao usuário: estrutura em
   módulos (`agent/state.py`, `agent/github_tool.py`, `agent/nodes.py`,
   `agent/graph.py`) vs. arquivo único. Escolhida a estrutura modular.
3. **Implementação dos nós** — cada nó foi descrito em linguagem natural
   antes de virar código: "`fetch_pr` valida entrada, chama a API do GitHub
   e marca `error` no estado se falhar; aresta condicional decide entre
   `analyze_files` e `handle_error`", etc.
4. **Teste com PR real** — "Rodar o agente contra 1–2 PRs reais para gerar
   exemplos verdadeiros de entrada/saída" (Fase 4 do plano), antecipado
   ainda durante a Fase 2 para validar a implementação de ponta a ponta.

## 4. Correções durante o desenvolvimento

- **Erro de saldo insuficiente (Anthropic API direta)**: o primeiro teste
  retornou `Your credit balance is too low to access the Anthropic API`.
  Prompt do usuário: *"Mode de claude para Openrouter, segue o ApiKey [...]"*
  — decisão de trocar o provedor do LLM de Anthropic direto para
  OpenRouter, mantendo o mesmo modelo (Claude).
- **Erro de `max_tokens` (OpenRouter)**: o segundo teste retornou
  `This request requires more credits, or fewer max_tokens. You requested
  up to 64000 tokens, but can only afford 7653`. Correção: limitar
  explicitamente `max_tokens=1024` na chamada ao modelo, já que a análise
  pedida (até 5 bullets por arquivo) não precisa de uma saída longa.

Esses dois erros reais (e as correções) estão documentados também na seção
"Decisões tomadas" do `README.md`.

## 5. Prompt operacional do agente (usado em `analyze_files`)

Este é o prompt que o próprio agente envia ao LLM, uma vez por arquivo
alterado do PR (`agent/nodes.py`):

```text
Você é um revisor de código sênior. Analise o diff abaixo do arquivo
"{filename}" e aponte, de forma objetiva e curta (até 5 bullets):
- bugs prováveis
- riscos (segurança, regressão, performance)
- sugestões de estilo/boas práticas

Se não houver nada relevante, responda apenas "Sem observações relevantes.".

Diff:
```
{patch}
```
```

`{filename}` e `{patch}` são preenchidos dinamicamente pelo estado do
grafo; `{patch}` é truncado em `MAX_PATCH_CHARS` (6000 caracteres) antes do
envio.
