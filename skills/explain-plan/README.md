# explain-plan

Explica um plano de feature de forma didática, para você entender e revisar antes de construir.

Você passa o caminho ou o link do plano: um `plan.md`, uma spec, um design doc ou a transcrição de uma conversa. A skill lê o plano, confere no código os pontos que vai apontar e devolve um overview em tópicos, como estrutura, contrato, estado, configuração, plataforma, ciclo de vida e escopo. Em cada tópico:

- **Decidido:** o que o plano já fechou.
- **Para revisar:** escolhas para reconfirmar, premissas sem confirmação e riscos.
- **Novo:** o que o plano nunca discutiu e a skill encontrou na leitura.

Quando um ponto depende de uma decisão sua, ela pergunta em texto, uma pergunta separada da outra. Usa Mermaid quando um conceito fica mais claro desenhado.

É só informativa: não implementa, não edita o plano e não inicia nenhuma etapa.

```
/explain-plan .notebook/specs/features/minha-feature/plan.md
```
