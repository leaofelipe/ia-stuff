# explain-plan

Explica um plano de feature de forma didática, para você entender o que ele define antes de construir.

Você passa o caminho ou o link do plano: um `plan.md`, uma spec, um design doc ou a transcrição de uma conversa. A skill lê o plano e devolve um overview em tópicos, como estrutura, contrato, estado, configuração, plataforma, ciclo de vida e escopo. Em cada tópico:

- Um parágrafo explica como aquela parte funciona e como se liga às outras.
- **O que o plano define:** os nomes e valores literais.
- **Por que assim:** a justificativa e as alternativas rejeitadas que o próprio plano registra.

A skill mostra o plano, não avalia: não aponta riscos, lacunas nem melhorias. Se você vir algo errado, traz o ponto, e aí ela confere e trabalha nele com você. As buscas no código (estado da branch, o que os componentes citados fazem hoje) vão para subagentes, para não poluir o chat principal. Usa Mermaid quando um conceito fica mais claro desenhado.

É só informativa: não implementa, não edita o plano e não inicia nenhuma etapa.

```
/explain-plan {your plan.md / link/ etc }
```
