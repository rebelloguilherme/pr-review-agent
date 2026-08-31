# Priorização de testes

O projeto tem testes de unidade e de integração/E2E cobrindo o fluxo
principal (`tests/`), mas o mais importante de todos, na nossa avaliação
de risco, é `tests/test_security.py::TestPostCommentGovernance`.

## Por que este é o teste prioritário

Critério: **impacto de uma falha**, não frequência de uso.

- Se um teste de "fluxo feliz" falhar (ex.: relatório mal formatado), o
  pior cenário é um relatório confuso — incômodo, mas reversível e visível
  na hora.
- Se `test_blocks_when_injection_detected_even_if_approved` falhar (ou
  fosse removido), o pior cenário é: um PR malicioso com prompt injection
  na descrição consegue fazer o agente publicar um comentário público no
  GitHub sem que isso devesse ter acontecido — um incidente de segurança
  real, silencioso (ninguém necessariamente percebe até o comentário já
  estar público), e com efeito visível para terceiros.

Em outras palavras: a maioria dos bugs neste projeto degrada a
*qualidade* da revisão. Uma falha neste guardrail especificamente degrada
a *segurança* da aplicação. Por isso ele roda isolado, é o primeiro teste
verificado na pipeline (ver `.github/workflows/ci.yml`) e qualquer PR que
toque `agent/security.py` ou `agent/nodes.py::post_comment` deveria
rodar esse arquivo de teste explicitamente antes do merge, não só confiar
na cobertura geral.

## Critério aplicado

Risco = probabilidade × impacto. A probabilidade de alguém abrir um PR
com uma descrição adversarial não é alta hoje (repositório pessoal, sem
tráfego externo), mas o **impacto** de uma falha aqui é o maior do
projeto — por isso o teste é prioritário mesmo sem um histórico de
incidentes reais.
