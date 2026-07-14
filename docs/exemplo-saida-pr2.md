# Revisão do PR: fix: elimina duplicação na montagem do histórico de produtos

- **Autor:** rebelloguilherme
- **Branch:** `fix/dry-historico-modificacoes` -> `main`
- **Arquivos analisados:** 3

## Descrição do PR
## Resumo
- A montagem do registro de histórico (`Descricao` formatada + demais campos de `ProdutoHistorico`) estava duplicada 4x: em `CriarAsync` e `AtualizarAsync`, tanto no `ProdutoEfService` quanto no `ProdutoDapperService`.
- Extraída para `ProdutoHistoricoFactory.Criar(produto, acao)`, reutilizada pelas duas trilhas.
- Nenhuma mudança de comportamento ou de contrato de API.

## Test plan
- [x] `dotnet build` sem erros/avisos
- [x] Testado via curl: criar/atualizar produto em ambas as trilhas (EF e Dapper) e conferir que o histórico retornado continua idêntico ao formato anterior

## Análise por arquivo
### `backend/src/CrudAntDesign.Application/Services/ProdutoDapperService.cs`
• **Bug provável**: Na linha do `AtualizarAsync`, usa `existente` em vez de `atualizado` para criar o histórico — pode registrar dados desatualizados se o repositório retornar um objeto diferente.

• **Risco de regressão**: A lógica de criação do histórico foi movida para `ProdutoHistoricoFactory.Criar()`, mas não há validação se essa factory está implementada corretamente ou se trata `DateTime.UtcNow` da mesma forma.

• **Boas práticas**: Excelente refatoração — reduz duplicação e centraliza a lógica. Considere adicionar testes unitários para `ProdutoHistoricoFactory.Criar()` para garantir consistência.

• **Sugestão**: Verifique se `ProdutoHistoricoFactory` está em namespace apropriado e se há injeção de dependência (se necessário para timestamps ou outras responsabilidades).

### `backend/src/CrudAntDesign.Application/Services/ProdutoEfService.cs`
• **Bug provável**: Na linha do `AtualizarAsync`, usa `existente` em vez de `atualizado` para criar o histórico — pode registrar dados desatualizados se houver divergência entre objeto local e banco.

• **Risco de regressão**: A lógica de formatação do histórico foi movida para `ProdutoHistoricoFactory.Criar()` sem validação visível — se a factory não existir ou falhar, quebrará a funcionalidade.

• **Boas práticas**: Excelente refatoração com Factory Pattern, reduzindo duplicação e melhorando manutenibilidade.

• **Sugestão**: Adicionar tratamento de erro/logging caso `ProdutoHistoricoFactory.Criar()` falhe, para não deixar a operação principal sem auditoria silenciosamente.

### `backend/src/CrudAntDesign.Application/Services/ProdutoHistoricoFactory.cs`
• **Risco de Null Reference**: Sem validação de `produto` nulo, causará `NullReferenceException` em produção.

• **Segurança - Injeção de Dados**: A `Descricao` concatena dados do usuário sem sanitização; considere usar `StringBuilder` ou parametrização se houver persistência em BD.

• **Performance**: String interpolation com formatação `C` é aceitável, mas se chamado em loop, considere cache ou lazy evaluation.

• **Boas Práticas**: Factory estático é apropriado, mas adicione validação básica (`ArgumentNullException`) no parâmetro `produto`.

• **Sugestão**: Considere adicionar validação do parâmetro `acao` (nulo/vazio) também.

## Conclusão
Foram identificados pontos de atenção acima — revisar antes do merge.