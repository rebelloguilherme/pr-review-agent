# Investigação de uma execução real — `rebelloguilherme/pr-review-agent#3`

Demonstração de como os dois sinais de observabilidade são usados juntos
para reconstruir o que aconteceu numa execução real, usando
`trace_id = "rebelloguilherme/pr-review-agent#3"` para correlacionar.

- Logs estruturados: [`logs-agent-exemplo.jsonl`](logs-agent-exemplo.jsonl) (35 linhas)
- Trilha de auditoria: [`audit-exemplo.jsonl`](audit-exemplo.jsonl) (4 linhas)
- Relatório final gerado: [`pr3-observabilidade-com-falso-positivo.md`](pr3-observabilidade-com-falso-positivo.md)

## O que os logs mostram (performance/fluxo)

`fetch_pr.start` → `fetch_pr.success` (14 arquivos, descrição do PR limpa
— nenhuma injection detectada nela) → 14x `analyze_one_file.start` /
`.success` / `.fallback` em paralelo (latências entre ~370ms e ~15s por
arquivo, evidenciando o paralelismo real: o tempo total da execução foi
37,5s, muito menor que a soma das latências individuais) →
`generate_report.start` → `post_comment.blocked_injection`.

## O que a trilha de auditoria mostra (governança) — a pergunta interessante

A trilha de auditoria aponta 3 eventos `prompt_injection_detected`, nos
arquivos `README.md`, `agent/security.py` e `tests/test_security.py` —
por isso o comentário final foi bloqueado (`comment_blocked`).

**Isso é um falso positivo real e explicável**: o PR nº3 é exatamente o
PR que *introduziu* o guardrail de prompt injection — então o diff desses
3 arquivos contém, literalmente, os textos de exemplo e os padrões
usados para detectar injection (ex.: a string `"ignore all instructions"`
aparece no próprio código de teste e na documentação). O detector,
sendo baseado em padrões de texto (não em entendimento semântico),
não distingue "este texto é uma tentativa de ataque" de "este texto
é um teste automatizado que menciona ataques".

## Conclusão da investigação

Correlacionando os dois sinais dá exatamente a resposta que se espera de
observabilidade: os logs mostram *que* o bloqueio aconteceu e em que
momento da execução; a auditoria mostra *por quê* (e em quais arquivos
específicos) — e juntos permitem diagnosticar que não é um bug de
segurança, é uma limitação conhecida e documentada do detector (ver
"Limitações" no README). Sem os dois sinais juntos, seria preciso
adivinhar a causa a partir só do relatório final.
