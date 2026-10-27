---
name: readable-code
description: Mapeia e melhora a legibilidade do código que mudou numa branch, sem alterar comportamento — expressões aninhadas, nomes sem significado, números mágicos, duplicação e comentários que explicam o "o quê". Use quando o usuário pedir para deixar o código legível, limpar a branch, reduzir aninhamento ou melhorar nomes antes do review ou merge.
---

# Código legível

Muda a forma do código, nunca o comportamento. Escopo: só o que mudou na branch (commits e alterações não commitadas), em código de produção. Siga as regras e convenções do projeto (AGENTS.md, README, lint).

Fluxo: **Plan → Checks → Build → Verify.** Pare no Plan; só faça o Build quando o usuário pedir explicitamente.

## Plan

Entregue uma tabela `arquivo:linha | trecho | proposta` e as renomeações `antigo → novo`, por impacto. Procure:

- **Aninhamento:** ternário dentro de ternário, de template string ou de argumento; `&&`/`||` como fluxo de controle; callback inline com decisão dentro.
- **Nomes:** vagos ou enganosos (`data`, `result`, `tmp`), booleano sem `is/has/can`, método sem verbo.
- **Outros:** números e strings mágicos, blocos repetidos, `let` com reatribuição condicional.
- **Comentários:** o "o quê" vira nome. O "porquê" não se apaga em silêncio: pergunte onde guardar (comentário curto ou doc do componente).

Termine perguntando se segue com tudo ou só parte.

## Checks

Rode os testes dos módulos afetados antes e anote a contagem; se já estiverem vermelhos, pare. Avise sobre trechos sem teste e sobre nomes referenciados por testes ou por outros módulos.

## Build

- Preserve o comportamento: ordem de chamadas e eventos, valores falsy, `undefined` vs argumento ausente.
- Não toque em API pública, nomes de eventos, payloads nem mensagens de erro.
- Não crie abstração de uso único, não adicione dependência, não conserte bug alheio (reporte).
- Teste só muda para acompanhar renomeação. Sem commit sem pedido.

## Verify

Mesmos testes, mesma contagem; lint e formatter; releia o diff procurando mudança de comportamento. Reporte curto: o que mudou, o que ficou de fora, o que conferir à mão.
