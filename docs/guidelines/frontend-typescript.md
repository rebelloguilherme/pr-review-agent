# Guia de revisão — Frontend (React / TypeScript)

## Tipagem
- Evitar `string`/`any` para campos que representam um conjunto fechado de valores (status, ação, tipo) — preferir union types ou enum, para o compilador pegar valores inválidos.
- Datas e horários vindos de API devem ter um tipo e formato consistentes (ISO 8601), documentados; não misturar `string` livre com `Date` no mesmo domínio.

## Tratamento de erros de rede
- Toda chamada a uma API (`fetch`, cliente HTTP) deve tratar o caminho de erro (4xx/5xx, timeout) — não assumir que a Promise sempre resolve com sucesso.
- Estados de carregamento e erro devem existir na UI para qualquer requisição assíncrona visível ao usuário.

## Organização de componentes
- Lógica de negócio (chamadas de API, transformação de dados, regras) que se repete em mais de um componente é candidata a um hook customizado.
- Componentes de tabela/lista grandes devem paginar ou virtualizar quando a fonte de dados pode crescer sem limite.

## Validação de entrada
- Parâmetros vindos de rota/props que alimentam uma chamada de API (IDs, filtros) devem ser validados antes do uso (ex.: não disparar requisição com ID inválido/negativo).
