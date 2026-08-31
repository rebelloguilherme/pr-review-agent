# Guia de revisão — Backend (.NET / C#)

## Tratamento de erros
- Todo endpoint que consulta um recurso por ID deve tratar o caso de "não encontrado" explicitamente (404), nunca deixar uma `NullReferenceException` estourar até o cliente.
- Chamadas a serviços externos (banco, APIs de terceiros) devem ter tratamento de exceção e retornar um erro estruturado, não vazar stack trace para o cliente.

## Autorização
- Toda ação que altera dados (criar, atualizar, excluir) deve validar permissão do usuário autenticado antes de executar — não confiar apenas em `[Authorize]` genérico quando há regras por dono do recurso.
- Nunca confiar em IDs vindos do corpo da requisição para autorização; validar contra o usuário autenticado no contexto.

## Consultas e performance
- Endpoints que retornam listas potencialmente grandes (histórico, logs, resultados de busca) devem ter paginação — não retornar tudo de uma vez.
- Evitar consultas N+1: se o código itera uma coleção fazendo 1 query por item, é um sinal de alerta.

## Padrões de resposta
- Manter consistência entre métodos: se a maioria dos métodos de um serviço retorna `Task<T>`, um método isolado que retorna `void`/`Task` sem motivo aparente merece observação.
