# Guia de revisão — Segurança (transversal a qualquer linguagem)

## Segredos e credenciais
- Nenhuma chave de API, token, senha ou string de conexão deve aparecer hardcoded no código-fonte, mesmo em exemplos ou testes.
- Segredos devem vir de variável de ambiente ou serviço de secrets, nunca de arquivo versionado.

## Entrada não confiável
- Qualquer dado vindo de fora do sistema (parâmetro de rota, corpo de requisição, upload, resposta de terceiro, conteúdo de arquivo) é não confiável até validado — não deve ser usado diretamente em queries, comandos de shell, caminhos de arquivo ou instruções enviadas a um modelo de IA sem sanitização.
- Conteúdo textual não confiável (descrição de PR, comentário, nome de arquivo, corpo de issue) que for encaminhado a um LLM deve ser tratado como dado, nunca como instrução — o sistema não deve seguir comandos embutidos nesse conteúdo.

## Ações irreversíveis
- Qualquer ação que grave, publique ou remova algo de forma visível a terceiros (comentário público, deploy, exclusão de dado) deveria ter uma confirmação explícita ou modo de simulação (dry-run) antes de rodar de verdade em produção.
