# Revisão do PR: feat: adiciona histórico de modificações de produtos

- **Autor:** rebelloguilherme
- **Branch:** `feat/historico-modificacoes` -> `main`
- **Arquivos analisados:** 23

## Descrição do PR
## Resumo
- Nova tabela `produto_historicos` registrando cada criação/atualização de produto (ação, descrição do snapshot e data/hora).
- Endpoint `GET /api/produtos-{ef|dapper}/{id}/historico` nas duas trilhas.
- Modal de linha do tempo no frontend (botão "Histórico" na tabela de produtos) para consultar as alterações.

## Test plan
- [x] `dotnet build` sem erros/avisos
- [x] `dotnet ef database update` aplicado com sucesso (nova tabela criada)
- [x] `npx tsc --noEmit` sem erros
- [x] `npx eslint` sem avisos nos arquivos alterados
- [x] Testado via curl: criar/atualizar produto em ambas as trilhas (EF e Dapper) e conferir histórico retornado
- [x] Testado via browser (Playwright): abrir modal de histórico nas abas EF Core e Dapper, conferir timeline renderizada corretamente

## Análise por arquivo
### `README.md`
Sem observações relevantes.

### `backend/src/CrudAntDesign.Api/Controllers/ProdutosDapperController.cs`
• **Falta tratamento de erro**: O método não valida se o produto existe antes de retornar o histórico; deveria retornar `NotFound()` se o ID for inválido

• **Risco de N+1 queries**: Sem contexto da implementação de `ObterHistoricoAsync()`, há risco de múltiplas queries ao banco se não usar `Include()` adequadamente

• **Sem paginação**: Retornar `IEnumerable` completo pode causar problemas de performance com grandes volumes de dados históricos

• **Inconsistência de padrão**: Outros métodos usam `if/else` explícito; este usa expressão lambda, quebrando consistência do controller

• **Falta validação de autorização**: Não há verificação se o usuário tem permissão para acessar o histórico deste produto

### `backend/src/CrudAntDesign.Api/Controllers/ProdutosEfController.cs`
• **Falta tratamento de erro**: `ObterHistoricoAsync` pode lançar exceção se `id` inválido; considere adicionar try-catch ou validação

• **Sem validação de entrada**: Falta `[Authorize]` ou validação se o usuário tem permissão para acessar histórico de outros produtos

• **Inconsistência de padrão**: Outros métodos retornam `NotFound()` quando recurso não existe; este sempre retorna `Ok()` mesmo se vazio

• **Sem paginação**: Se histórico for grande, retornar `IEnumerable` completo pode impactar performance; considere adicionar `skip/take`

• **Falta documentação**: Sem `[ProducesResponseType]` ou comentários XML para documentar possíveis respostas (200, 404, 401)

### `backend/src/CrudAntDesign.Application/DTOs/ProdutoHistoricoDto.cs`
• **Falta validação**: `Acao` e `Descricao` aceitam strings vazias; considere usar `[Required]` e `[StringLength]` para garantir dados válidos

• **Sem nullable annotations**: Propriedades `string` deveriam ser explicitamente `string?` ou usar `#nullable enable` para evitar null reference exceptions

• **DataHora sem timezone**: `DateTime` sem especificação pode causar inconsistências; considere usar `DateTime.UtcNow` ou `DateTimeOffset`

• **Falta de imutabilidade**: DTO deveria ter `init` em vez de `set` para evitar modificações acidentais após criação

• **Sem versionamento**: Se esta DTO será exposta em API, considere adicionar versionamento para compatibilidade futura

### `backend/src/CrudAntDesign.Application/Interfaces/IProdutoDapperRepository.cs`
• **Falta de documentação XML**: Os novos métodos não possuem comentários explicando propósito, parâmetros e retorno (padrão da interface existente).

• **Inconsistência de nomenclatura**: `AdicionarHistoricoAsync` usa padrão português enquanto outros métodos usam inglês (`Add`, `Update`, `Delete`).

• **Falta de retorno em AdicionarHistoricoAsync**: Método não retorna confirmação de sucesso (bool/id), dificultando tratamento de erros na camada de aplicação.

• **Sem validação de entrada**: `GetHistoricoAsync` não documenta comportamento com `produtoId` inválido ou inexistente.

• **Possível N+1 query**: Considere adicionar paginação/filtros ao `GetHistoricoAsync` para evitar problemas de performance com históricos grandes.

### `backend/src/CrudAntDesign.Application/Interfaces/IProdutoDapperService.cs`
• **Falta validação de entrada**: O parâmetro `produtoId` não tem validação explícita; considere documentar o comportamento esperado para IDs inválidos (≤ 0).

• **Inconsistência de nomenclatura**: Outros métodos usam `id`, mas este usa `produtoId`; padronizar para `id` mantém consistência.

• **Sem tratamento de erro documentado**: A interface não documenta se retorna coleção vazia ou lança exceção quando produto não existe.

• **Possível N+1 query**: Dependendo da implementação, `ObterHistoricoAsync` pode gerar múltiplas queries; considere adicionar parâmetros de paginação.

• **Sugestão**: Adicionar documentação XML (`/// <summary>`) para clareza sobre comportamento e retorno esperado.

### `backend/src/CrudAntDesign.Application/Interfaces/IProdutoEfRepository.cs`
• **Falta de documentação XML**: Os novos métodos carecem de comentários explicando propósito, parâmetros e retorno (padrão da interface existente).

• **Inconsistência de nomenclatura**: `AdicionarHistoricoAsync` usa padrão português enquanto `GetHistoricoAsync` usa inglês; considere padronizar (recomendado: `AddHistoricoAsync` ou `GetHistoricAsync`).

• **Falta de tratamento de erro**: `AdicionarHistoricoAsync` não retorna `Task<bool>` para indicar sucesso/falha, diferente de `UpdateAsync` e `DeleteAsync`.

• **Risco de N+1 queries**: `GetHistoricoAsync` retorna `IEnumerable` sem paginação; pode causar problemas de performance com grandes volumes de dados.

• **Validação ausente**: Não há indicação se `produtoId` inválido ou `historico` nulo são tratados na implementação.

### `backend/src/CrudAntDesign.Application/Interfaces/IProdutoEfService.cs`
• **Falta validação de entrada**: O parâmetro `produtoId` não tem validação explícita; considere documentar comportamento para IDs inválidos/inexistentes

• **Inconsistência de nomenclatura**: Método usa `produtoId` enquanto outros usam `id`; padronizar para manter consistência

• **Sem tratamento de erro documentado**: Interface não especifica se retorna coleção vazia ou lança exceção quando produto não existe

• **Performance**: `IEnumerable` permite lazy loading; considere `IAsyncEnumerable` para grandes volumes de histórico ou adicionar paginação

• **Sugestão de documentação**: Adicionar XML comments explicando o comportamento esperado (ordenação, filtros, limites)

### `backend/src/CrudAntDesign.Application/Services/ProdutoDapperService.cs`
• **Bug provável**: `ExcluirAsync` não registra histórico como as outras operações, criando inconsistência na auditoria.

• **Risco de regressão**: Operações de histórico não possuem tratamento de erro/transação — falha ao salvar histórico não impede a operação principal, deixando dados inconsistentes.

• **Risco de segurança**: Descrição do histórico expõe dados sensíveis (preços, estoque) em texto livre sem validação ou mascaramento.

• **Performance**: Chamadas assíncronas sequenciais (`UpdateAsync` → `AdicionarHistoricoAsync`) — considere usar transação ou padrão Unit of Work.

• **Estilo**: Strings de ação ("Criado", "Atualizado") devem ser constantes/enum para evitar erros de digitação e facilitar manutenção.

### `backend/src/CrudAntDesign.Application/Services/ProdutoEfService.cs`
• **Bug provável**: `ExcluirAsync` não registra histórico como as outras operações, criando inconsistência na auditoria.

• **Risco de regressão**: Novos métodos no repositório (`AdicionarHistoricoAsync`, `GetHistoricoAsync`) não foram validados; falta verificar se existem e funcionam corretamente.

• **Risco de performance**: Strings de descrição com interpolação podem ficar muito grandes; considerar limitar tamanho ou armazenar apenas IDs/deltas.

• **Boas práticas**: Extrair lógica de criação do histórico para método privado reutilizável (DRY) - está duplicada em `CriarAsync` e `AtualizarAsync`.

• **Segurança**: Validar se `ProdutoHistoricoDto` expõe dados sensíveis; considerar adicionar auditoria de *quem* fez a alteração (usuário/IP).

### `backend/src/CrudAntDesign.Domain/Entities/ProdutoHistorico.cs`
• **Bug provável**: `DateTime DataHora = DateTime.UtcNow` é avaliado em tempo de compilação, não de instância. Use `DateTime.UtcNow` no construtor ou property initializer dinâmico.

• **Risco de segurança**: `Acao` e `Descricao` sem validação de tamanho máximo podem causar SQL injection ou overflow no banco de dados.

• **Falta de relacionamento**: `ProdutoId` é uma FK sem navegação para `Produto` — adicione a propriedade de navegação.

• **Boas práticas**: Adicione validações com `[Required]`, `[MaxLength]` e considere um construtor explícito para inicializar `DataHora` corretamente.

• **Performance**: Sem índice em `ProdutoId`, queries de histórico por produto serão lentas em grandes volumes.

### `backend/src/CrudAntDesign.Infrastructure/Data/AppDbContext.cs`
• **Falta validação de entidade**: `ProdutoHistorico` foi adicionado ao contexto, mas não há garantia de que a classe existe ou está mapeada corretamente — verifique se `ProdutoHistoricoMapping` está implementada.

• **Sem relacionamento definido**: Se `ProdutoHistorico` é um histórico de `Produto`, falta configurar o relacionamento (FK, cascade delete, etc.) na mapping.

• **Possível regressão em migrations**: Adicionar nova entidade sem migration pode causar inconsistência entre código e banco — gere migration correspondente.

• **Sem índices de performance**: Tabelas de histórico geralmente crescem muito; considere adicionar índices na mapping (ex: `HasIndex(x => x.ProdutoId)` e `HasIndex(x => x.DataCriacao)`).

### `backend/src/CrudAntDesign.Infrastructure/Data/Mappings/ProdutoHistoricoMapping.cs`
• **Falta configuração de relacionamento**: Não há mapeamento da chave estrangeira para `Produto` (presumivelmente existe), o que pode causar erro de integridade referencial.

• **Sem índices**: Considere adicionar índice em `DataHora` e/ou `ProdutoId` para melhorar performance em queries de histórico.

• **Tipo de dado não especificado**: `DataHora` deveria usar `.HasColumnType("datetime2")` ou similar para garantir precisão temporal consistente.

• **Sem auditoria de criação**: Faltam campos como `CriadoEm` ou `CriadoPor` típicos em tabelas de histórico.

### `backend/src/CrudAntDesign.Infrastructure/Migrations/20260713233919_CriarTabelaProdutoHistoricos.Designer.cs`
Análise indisponível para este arquivo após novas tentativas (erro: Error code: 402 - {'error': {'message': 'This request would exceed your available credits given your current in-flight requests. Retry after in-flight requests settle, or add credits.', 'code': 402, 'metadata': {'reason': 'in_flight_budget_exhausted', 'limit_source': 'openrouter_in_flight_budget', 'remedy_hint': 'Retry after your in-flight requests settle (see the Retry-After header). Adding credits at https://openrouter.ai/settings/credits raises your in-flight budget, up to a capped ceiling.', 'headers': {'Retry-After': '120'}, 'provider_name': None}}, 'user_id': 'user_3EbQ1KJZoWZa5a9msqFHNWGzvqI'}).

### `backend/src/CrudAntDesign.Infrastructure/Migrations/20260713233919_CriarTabelaProdutoHistoricos.cs`
• **Falta Foreign Key**: `ProdutoId` não possui constraint de chave estrangeira para a tabela `produtos`, permitindo referências órfãs.

• **Sem índice em ProdutoId**: Campo frequentemente consultado deveria ter índice para melhor performance em queries de histórico.

• **DataHora sem valor padrão**: Deveria usar `DateTime.UtcNow` como padrão no banco para garantir preenchimento automático.

• **Sem auditoria de usuário**: Falta campo para rastrear qual usuário realizou a ação (boas práticas de auditoria).

• **Descricao muito genérica**: Campo de 500 caracteres pode ser insuficiente; considere aumentar ou documentar o limite esperado.

### `backend/src/CrudAntDesign.Infrastructure/Migrations/AppDbContextModelSnapshot.cs`
• **Falta de Foreign Key**: A propriedade `ProdutoId` não possui configuração de relacionamento (`.HasForeignKey()` ou `.WithMany()`), causando potencial inconsistência referencial no banco.

• **Sem índice em ProdutoId**: Recomenda-se adicionar `.HasIndex("ProdutoId")` para otimizar queries de filtro por produto.

• **DateTime sem timezone**: `DataHora` sem especificação de timezone pode causar inconsistências em ambientes distribuídos; considere usar `HasConversion` ou documentar o padrão.

• **Sem auditoria de usuário**: Falta campo de `UsuarioId` ou similar para rastrear quem fez a ação (boas práticas de auditoria).

### `backend/src/CrudAntDesign.Infrastructure/Repositories/ProdutoDapperRepository.cs`
• **Bug provável**: `GetHistoricoAsync` retorna `IEnumerable<T>` de uma conexão já fechada (após `using`). Dapper materializa lazy, causando erro ao iterar. Converter para `List<T>` ou `ToList()`.

• **Risco de segurança**: Sem validação de entrada em `produtoId`. Adicionar guard clause para valores inválidos (≤ 0).

• **Inconsistência**: `AdicionarHistoricoAsync` não retorna ID gerado. Considerar retornar `int` para rastreabilidade.

• **Boas práticas**: Métodos novos não possuem testes unitários aparentes. Adicionar testes para ambos os métodos.

• **Performance**: Sem índice mencionado em `produto_historicos.ProdutoId`. Verificar se existe índice para otimizar a query `WHERE`.

### `backend/src/CrudAntDesign.Infrastructure/Repositories/ProdutoEfRepository.cs`
Análise indisponível para este arquivo após novas tentativas (erro: Error code: 402 - {'error': {'message': 'This request would exceed your available credits given your current in-flight requests. Retry after in-flight requests settle, or add credits.', 'code': 402, 'metadata': {'reason': 'in_flight_budget_exhausted', 'limit_source': 'openrouter_in_flight_budget', 'remedy_hint': 'Retry after your in-flight requests settle (see the Retry-After header). Adding credits at https://openrouter.ai/settings/credits raises your in-flight budget, up to a capped ceiling.', 'headers': {'Retry-After': '120'}, 'provider_name': None}}, 'user_id': 'user_3EbQ1KJZoWZa5a9msqFHNWGzvqI'}).

### `frontend/src/features/produtos/ProdutoHistoricoModal.tsx`
Análise indisponível para este arquivo após novas tentativas (erro: Error code: 402 - {'error': {'message': 'This request would exceed your available credits given your current in-flight requests. Retry after in-flight requests settle, or add credits.', 'code': 402, 'metadata': {'reason': 'in_flight_budget_exhausted', 'limit_source': 'openrouter_in_flight_budget', 'remedy_hint': 'Retry after your in-flight requests settle (see the Retry-After header). Adding credits at https://openrouter.ai/settings/credits raises your in-flight budget, up to a capped ceiling.', 'headers': {'Retry-After': '120'}, 'provider_name': None}}, 'user_id': 'user_3EbQ1KJZoWZa5a9msqFHNWGzvqI'}).

### `frontend/src/features/produtos/ProdutosCrud.tsx`
Análise indisponível para este arquivo após novas tentativas (erro: Error code: 402 - {'error': {'message': 'This request would exceed your available credits given your current in-flight requests. Retry after in-flight requests settle, or add credits.', 'code': 402, 'metadata': {'reason': 'in_flight_budget_exhausted', 'limit_source': 'openrouter_in_flight_budget', 'remedy_hint': 'Retry after your in-flight requests settle (see the Retry-After header). Adding credits at https://openrouter.ai/settings/credits raises your in-flight budget, up to a capped ceiling.', 'headers': {'Retry-After': '120'}, 'provider_name': None}}, 'user_id': 'user_3EbQ1KJZoWZa5a9msqFHNWGzvqI'}).

### `frontend/src/features/produtos/ProdutosTable.tsx`
Análise indisponível para este arquivo após novas tentativas (erro: Error code: 402 - {'error': {'message': 'This request would exceed your available credits given your current in-flight requests. Retry after in-flight requests settle, or add credits.', 'code': 402, 'metadata': {'reason': 'in_flight_budget_exhausted', 'limit_source': 'openrouter_in_flight_budget', 'remedy_hint': 'Retry after your in-flight requests settle (see the Retry-After header). Adding credits at https://openrouter.ai/settings/credits raises your in-flight budget, up to a capped ceiling.', 'headers': {'Retry-After': '120'}, 'provider_name': None}}, 'user_id': 'user_3EbQ1KJZoWZa5a9msqFHNWGzvqI'}).

### `frontend/src/features/produtos/produtosApiFactory.ts`
Análise indisponível para este arquivo após novas tentativas (erro: Error code: 402 - {'error': {'message': 'This request would exceed your available credits given your current in-flight requests. Retry after in-flight requests settle, or add credits.', 'code': 402, 'metadata': {'reason': 'in_flight_budget_exhausted', 'limit_source': 'openrouter_in_flight_budget', 'remedy_hint': 'Retry after your in-flight requests settle (see the Retry-After header). Adding credits at https://openrouter.ai/settings/credits raises your in-flight budget, up to a capped ceiling.', 'headers': {'Retry-After': '120'}, 'provider_name': None}}, 'user_id': 'user_3EbQ1KJZoWZa5a9msqFHNWGzvqI'}).

### `frontend/src/types/produto.ts`
• **Tipo de `acao` muito genérico**: usar `string` permite valores inválidos; considere usar `enum` (ex: `'CRIADO' | 'ATUALIZADO' | 'DELETADO'`)

• **`dataHora` como string**: propenso a inconsistências de formato; use `Date` ou `ISO 8601` com validação

• **Falta de validação**: sem `@IsNotEmpty()`, `@IsNumber()` etc. (se usar class-validator); considere adicionar decoradores

• **Campo `descricao` sem limite**: pode causar problemas de performance/storage; adicione `maxLength`

• **Sem timestamp de criação do registro**: considere adicionar `criadoEm` para auditoria completa

## Conclusão
Foram identificados pontos de atenção acima — revisar antes do merge.