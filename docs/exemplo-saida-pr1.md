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
• **Falta tratamento de erro**: O método não valida se o produto existe antes de retornar o histórico (risco de retornar 200 com lista vazia quando deveria ser 404)

• **Sem paginação**: Histórico pode crescer indefinidamente; considerar adicionar `skip`/`take` para grandes volumes de dados

• **Falta autorização**: Não há `[Authorize]` ou validação de permissão; qualquer usuário pode acessar histórico de qualquer produto

• **Inconsistência com padrão**: Outros métodos retornam `IActionResult`; este retorna `ActionResult<T>` (menor flexibilidade para tratamento de erros)

• **Sem logging**: Operação sensível (auditoria) deveria registrar acessos ao histórico

### `backend/src/CrudAntDesign.Api/Controllers/ProdutosEfController.cs`
• **Falta tratamento de erro**: `ObterHistoricoAsync` pode lançar exceção ou retornar null; sem try-catch, pode gerar 500 em vez de 404/400

• **Sem validação de entrada**: `id` não é validado; deveria verificar se é válido antes de chamar o serviço

• **Risco de N+1 queries**: Sem contexto do serviço, `ObterHistoricoAsync` pode fazer múltiplas queries; considere eager loading

• **Inconsistência com padrão existente**: Outros métodos usam `if/else` explícito; este usa expressão lambda - manter consistência

• **Falta autorização**: Sem `[Authorize]` ou validação, qualquer usuário acessa histórico de qualquer produto

### `backend/src/CrudAntDesign.Application/DTOs/ProdutoHistoricoDto.cs`
• **Falta validação**: `Acao` e `Descricao` sem limite de tamanho podem causar problemas de storage/performance; considere adicionar `[MaxLength]`

• **DataHora sem timezone**: `DateTime` sem especificação pode gerar inconsistências em ambientes distribuídos; use `DateTime.UtcNow` ou `DateTimeOffset`

• **Sem data annotations**: Faltam `[Required]` nos campos obrigatórios para validação automática no pipeline

• **Sem documentação**: Adicione XML comments (`///`) para documentar a DTO, especialmente o propósito de cada campo

• **Boas práticas**: Considere usar `init` em vez de `set` para imutabilidade: `public int Id { get; init; }`

### `backend/src/CrudAntDesign.Application/Interfaces/IProdutoDapperRepository.cs`
• **Falta de documentação XML**: Os novos métodos não possuem comentários explicando propósito, parâmetros e retorno (padrão da interface).

• **Inconsistência de nomenclatura**: `AdicionarHistoricoAsync` usa PascalCase português enquanto outros métodos usam inglês (`Add`, `Update`, `Delete`).

• **Falta de tratamento de erro**: `GetHistoricoAsync` não especifica comportamento quando `produtoId` é inválido ou não existe.

• **Retorno genérico demais**: `IEnumerable<ProdutoHistorico>` sem paginação pode causar problemas de performance com grandes volumes de dados.

• **Método sem retorno**: `AdicionarHistoricoAsync` não retorna confirmação de sucesso/falha (considerar `Task<bool>` para consistência).

### `backend/src/CrudAntDesign.Application/Interfaces/IProdutoDapperService.cs`
• **Falta validação de entrada**: O parâmetro `produtoId` não tem validação explícita; considere documentar comportamento para IDs inválidos (≤ 0)

• **Inconsistência de nomenclatura**: Outros métodos usam `id`, mas este usa `produtoId`; padronizar para `id` mantém consistência

• **Sem tratamento de erro documentado**: Não está claro se retorna coleção vazia ou lança exceção quando produto não existe

• **Performance**: Sem paginação em `IEnumerable`; históricos podem crescer indefinidamente causando problemas de memória

• **Sugestão**: Adicionar `[NotNull]` ou validação no contrato, considerar `IAsyncEnumerable<T>` ou paginação para grandes volumes

### `backend/src/CrudAntDesign.Application/Interfaces/IProdutoEfRepository.cs`
• **Falta de documentação**: Novos métodos sem XML comments dificultam compreensão de contrato e uso pela aplicação

• **Inconsistência de nomenclatura**: `AdicionarHistoricoAsync` (português) vs `GetHistoricoAsync` (misto) vs `AddAsync`/`DeleteAsync` (inglês) - padronizar

• **Falta de tratamento de erro**: `AdicionarHistoricoAsync` não retorna indicador de sucesso/falha, diferente dos outros métodos da interface

• **Possível N+1 query**: `GetHistoricoAsync` pode gerar múltiplas queries se não houver eager loading configurado - considerar adicionar parâmetro de paginação

• **Validação ausente**: Sem validação de `produtoId` ou `historico` nulos - considerar adicionar em contrato ou documentar comportamento esperado

### `backend/src/CrudAntDesign.Application/Interfaces/IProdutoEfService.cs`
• **Falta validação de entrada**: O parâmetro `produtoId` não tem validação explícita; considere documentar o comportamento esperado para IDs inválidos ou negativos.

• **Inconsistência de nomenclatura**: O parâmetro é `produtoId` enquanto outros métodos usam apenas `id`; padronizar para manter consistência.

• **Sem tratamento de erro documentado**: A interface não documenta se o método lança exceção quando o produto não existe ou retorna coleção vazia.

• **Possível problema de performance**: `IEnumerable` pode causar múltiplas iterações; considerar `IList<ProdutoHistoricoDto>` ou `List<ProdutoHistoricoDto>` se houver múltiplos acessos.

• **Falta de paginação**: Históricos podem crescer indefinidamente; considerar adicionar parâmetros de paginação (skip/take).

### `backend/src/CrudAntDesign.Application/Services/ProdutoDapperService.cs`
• **Bug provável**: `ExcluirAsync` não registra histórico como os outros métodos, criando inconsistência na auditoria.

• **Risco de regressão**: Novo método `AdicionarHistoricoAsync` não foi testado; falha silenciosa pode deixar histórico incompleto sem alertar.

• **Risco de performance**: Duas operações de banco (insert + histórico) sem transação; se a segunda falhar, dados ficam inconsistentes.

• **Segurança/Boas práticas**: Descrição do histórico concatenada manualmente é frágil; considere usar `JsonConvert.SerializeObject()` para capturar mudanças estruturadas.

• **Estilo**: Falta injeção de dependência ou factory para `ProdutoHistorico`; lógica de auditoria deveria estar em um serviço separado (SRP).

### `backend/src/CrudAntDesign.Application/Services/ProdutoEfService.cs`
• **Bug provável**: `ExcluirAsync` não registra histórico como os outros métodos, criando inconsistência na auditoria.

• **Risco de regressão**: Novos métodos `AdicionarHistoricoAsync` e `GetHistoricoAsync` no repositório não foram validados; podem não existir ou ter assinatura diferente.

• **Risco de performance**: Descrição do histórico concatena múltiplos campos formatados; considere usar `StringBuilder` ou objeto estruturado para grandes volumes.

• **Segurança/Boas práticas**: Strings de ação ("Criado", "Atualizado") devem ser constantes ou enum para evitar typos e facilitar manutenção.

• **Sugestão de estilo**: Extrair lógica de criação do histórico para método privado reutilizável (`CriarHistorico()`) para reduzir duplicação.

### `backend/src/CrudAntDesign.Domain/Entities/ProdutoHistorico.cs`
• **Bug provável**: `DateTime DataHora = DateTime.UtcNow` é avaliado em tempo de compilação, não de instanciação. Use `DateTime.UtcNow` em um construtor ou property initializer dinâmico.

• **Risco de segurança**: `Acao` e `Descricao` sem validação de tamanho máximo podem causar SQL injection ou overflow no banco de dados.

• **Falta de relacionamento**: `ProdutoId` é uma FK sem navegação para `Produto`. Adicione `public Produto Produto { get; set; }` para integridade referencial.

• **Boas práticas**: Adicione validações com `[Required]`, `[MaxLength]` e considere usar `required` keyword (C# 11+) para propriedades obrigatórias.

• **Auditoria**: Considere adicionar `UsuarioId` ou `Usuario` para rastrear quem fez a ação no histórico.

### `backend/src/CrudAntDesign.Infrastructure/Data/AppDbContext.cs`
• **Falta validação de entidade**: `ProdutoHistorico` foi adicionado ao contexto, mas não há garantia de que a classe existe ou está mapeada corretamente — verifique se `ProdutoHistoricoMapping` está implementada.

• **Sem relacionamento explícito**: Se `ProdutoHistorico` é histórico de `Produto`, considere adicionar relacionamento (FK) e configurar cascade delete/soft delete na mapping.

• **Possível falta de migrations**: A adição de nova tabela requer migration — confirme se foi gerada (`dotnet ef migrations add AddProdutoHistorico`).

• **Sem índices de performance**: Tabelas de histórico geralmente crescem rapidamente — considere adicionar índices na `ProdutoHistoricoMapping` (ex: data, produto_id).

### `backend/src/CrudAntDesign.Infrastructure/Data/Mappings/ProdutoHistoricoMapping.cs`
Sem observações relevantes.

### `backend/src/CrudAntDesign.Infrastructure/Migrations/20260713233919_CriarTabelaProdutoHistoricos.Designer.cs`
• **Falta de Foreign Key**: A entidade `ProdutoHistorico` possui `ProdutoId` mas não há definição de relacionamento/constraint com `Produto`. Isso pode causar inconsistência de dados.

• **Sem índice em ProdutoId**: Campo `ProdutoId` deveria ter um índice para melhorar performance em queries de histórico por produto.

• **DataHora sem valor padrão**: `DataHora` em `ProdutoHistorico` não possui `HasDefaultValueSql()`, podendo gerar registros com datas nulas se não preenchidas na aplicação.

• **Arquivo auto-gerado**: Lembrar que este arquivo é gerado automaticamente pelo EF Core - as correções devem ser feitas na migration `.cs` correspondente, não aqui.

### `backend/src/CrudAntDesign.Infrastructure/Migrations/20260713233919_CriarTabelaProdutoHistoricos.cs`
• **Falta Foreign Key**: `ProdutoId` não possui constraint de chave estrangeira para a tabela `produtos`, permitindo referências órfãs.

• **Sem índice em ProdutoId**: Campo frequentemente consultado deveria ter índice para melhor performance em queries de histórico.

• **DataHora sem valor padrão**: Deveria usar `DateTime.UtcNow` como padrão no banco para garantir preenchimento automático.

• **Sem auditoria de usuário**: Falta campo para rastrear qual usuário realizou a ação (importante para compliance).

• **Descricao muito genérica**: Campo de 500 caracteres pode ser insuficiente; considere aumentar ou documentar o limite esperado.

### `backend/src/CrudAntDesign.Infrastructure/Migrations/AppDbContextModelSnapshot.cs`
• **Falta de Foreign Key**: A propriedade `ProdutoId` não possui configuração de relacionamento (`.HasForeignKey()` ou `.WithMany()`), causando potencial inconsistência referencial no banco.

• **Sem índice em ProdutoId**: Recomenda-se adicionar `.HasIndex("ProdutoId")` para otimizar queries de filtro por produto.

• **DataHora sem valor padrão**: Considere adicionar `.HasDefaultValueSql("CURRENT_TIMESTAMP(6)")` para auditoria automática.

• **Sem constraint de exclusão**: Defina comportamento de exclusão em cascata (`.OnDelete(DeleteBehavior.Cascade)`) se necessário manter histórico ou evitar órfãos.

### `backend/src/CrudAntDesign.Infrastructure/Repositories/ProdutoDapperRepository.cs`
• **Bug provável**: `GetHistoricoAsync` retorna `IEnumerable<T>` de uma conexão já fechada (using). Dapper materializa lazy, causando erro ao iterar. Use `ToList()` ou retorne `List<ProdutoHistorico>`.

• **Risco de segurança**: Sem validação de entrada em `AdicionarHistoricoAsync` — `historico` pode ser nulo ou conter dados inválidos. Adicione validações.

• **Inconsistência**: `AdicionarHistoricoAsync` não retorna nada (void async). Considere retornar o ID inserido ou um bool de sucesso para consistência com outros métodos.

• **Boas práticas**: Ambos os métodos abrem conexão manualmente. Se há `_connectionFactory`, considere centralizar em um método privado para evitar duplicação.

• **Performance**: `GetHistoricoAsync` sem paginação pode retornar muitos registros. Adicione limite ou paginação.

### `backend/src/CrudAntDesign.Infrastructure/Repositories/ProdutoEfRepository.cs`
• **Bug provável**: `GetHistoricoAsync` retorna `IEnumerable<ProdutoHistorico>` mas executa `.ToListAsync()`, causando inconsistência de tipo (deveria ser `Task<List<ProdutoHistorico>>` ou remover o `ToListAsync()`).

• **Risco de performance**: Sem paginação em `GetHistoricoAsync`, pode carregar milhares de registros em memória se o histórico for grande.

• **Risco de segurança**: Nenhuma validação se `produtoId` existe ou se o usuário tem permissão para acessar esse histórico.

• **Boas práticas**: `AdicionarHistoricoAsync` deveria retornar o objeto criado (com ID gerado) para melhor rastreabilidade.

• **Consistência**: Considerar usar `.AsNoTracking()` em `GetHistoricoAsync` já que é apenas leitura, melhorando performance.

### `frontend/src/features/produtos/ProdutoHistoricoModal.tsx`
• **Bug provável**: `formatarDataHora()` não trata datas inválidas — pode gerar "Invalid Date" se `item.dataHora` for malformado.

• **Risco de performance**: Sem `key` nos itens do Timeline — pode causar re-renders desnecessários se o array mudar de ordem.

• **Segurança**: `produtoNome` não é sanitizado — se vier de fonte não confiável, pode permitir XSS (embora Ant Design mitigue parcialmente).

• **Boas práticas**: `formatarDataHora()` deveria estar em arquivo utilitário separado, não no componente.

• **Sugestão**: Adicionar `loading` visual no Timeline ou desabilitar interações enquanto `loading === true` — atualmente o estado não afeta o conteúdo.

### `frontend/src/features/produtos/ProdutosCrud.tsx`
• **Bug provável**: Em `handleVerHistorico`, o modal abre antes de validar se `produto.id` existe, podendo causar requisição com ID inválido.

• **Risco de regressão**: Novos estados (`isHistoricoModalOpen`, `produtoDoHistorico`, `historico`, `carregandoHistorico`) aumentam complexidade; falta verificar se `ProdutosTable` foi atualizado para passar `onVerHistorico`.

• **Performance**: Sem limpeza de estado — ao fechar o modal, `historico` e `produtoDoHistorico` permanecem na memória; considere limpar em `onFechar`.

• **Boas práticas**: Falta tratamento específico do erro em `handleVerHistorico` (catch genérico); adicione logs ou diferencie tipos de erro.

• **Segurança**: Validar se `api.obterHistorico()` retorna dados esperados antes de usar em `setHistorico()`.

### `frontend/src/features/produtos/ProdutosTable.tsx`
• **Falta validação**: `onVerHistorico` não valida se `produto` é válido antes de chamar a função callback

• **Sem tratamento de erro**: Clique no botão "Histórico" pode falhar silenciosamente se a função callback não tratar exceções

• **Sem key em lista**: Se há múltiplos botões em `Space`, considere adicionar `key` props para evitar warnings do React

• **Boas práticas**: Extrair o botão "Histórico" para um componente separado (similar a `ConfirmDeleteButton`) para melhor manutenibilidade

• **Performance**: Sem `useMemo` nas colunas, elas são recriadas a cada render — considere memoizar se a tabela é grande

### `frontend/src/features/produtos/produtosApiFactory.ts`
• **Falta tratamento de erro**: O novo método `obterHistorico` não trata possíveis erros da requisição (404, 500, etc.), diferente do padrão esperado.

• **Inconsistência de retorno**: Métodos como `atualizar` e `excluir` retornam `Promise<void>`, mas `obterHistorico` retorna dados — considere documentar ou padronizar o padrão de resposta.

• **Type safety**: Validar se `ProdutoHistorico` está corretamente exportado em `../../types/produto` para evitar erros em tempo de execução.

• **Sugestão de estilo**: Manter consistência — outros métodos usam destructuring inline (`{ data }`), mas alguns poderiam beneficiar de comentários JSDoc para a nova funcionalidade.

### `frontend/src/types/produto.ts`
• **Type de data inadequado**: `dataHora: string` deveria ser `Date` para melhor type-safety e evitar bugs de parsing/formatação

• **Campo `acao` muito genérico**: usar `enum` ou `union type` (`'criacao' | 'atualizacao' | 'delecao'`) para garantir valores válidos

• **Falta de timestamps**: considerar adicionar `criadoEm` ou `atualizadoEm` para auditoria completa

• **Sem validação de relacionamento**: `produtoId` deveria ter comentário indicando se é obrigatório e se há validação de FK no backend

## Conclusão
Foram identificados pontos de atenção acima — revisar antes do merge.