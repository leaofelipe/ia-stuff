---
name: to-story
description: Turn a discovery dump, agent-generated text, existing Jira card, or one-line idea into a short human-readable Jira story. Use when the user says to-story, /to-story, or asks to draft, sanitize, or rewrite a card for a PO or a developer.
license: MIT
disable-model-invocation: true
---

Turn source material into a Jira story a PO could have written and a developer can pick up. The story says what is expected, not how to build it. Do not write files, never write to Jira without the user's explicit approval, and do not invent business justification.

## Tool check

Before anything else, check which Jira tool is available, in this order, and keep the first one found. A tool counts only when it is installed and authenticated; if either check fails, move to the next one.

1. Atlassian `twg` CLI: `command -v twg`, then `twg whoami` returns the current user.
2. Atlassian `acli` CLI: `command -v acli`, then `acli jira auth status` reports authenticated.
3. Any Atlassian MCP available in the session and not waiting for authentication.

The result sets the output mode for the whole run:

- **Jira mode** — a tool was found. It is used to read cards and, only after approval, to write them.
- **Markdown mode** — nothing was found. Cards are pasted by the user, and delivery ends with the Copy & Paste block in the Output reference shape.

## Style

This skill relies heavily on the `humanizer` skill. If it is available, run it in embedded mode on the final prose. If it is not, apply this checklist and continue: no emojis, no em or en dashes, no bold-header lists, no rule of three, no promotional language, no generic closing. This skill must work without `humanizer`.

## Inputs

Accept pasted text, a Jira key or URL, a file path, or a one-line idea. The usual case is a large discovery dump or agent-written text full of HOW.

When the input is a card, read it with the tool from Tool check. In Markdown mode, ask the user to paste the text.

Never fetch the URL. Never open a browser. From a board URL, take the `selectedIssue` key. Read title, description, and subtasks only. Ignore comments.

## Ask before drafting

If Context, Objective, and Acceptance criteria are already answerable from the source, draft immediately. A one-line idea always starts with questions.

Otherwise interview in this format, one round at a time, no question cap. Wait for answers before the next round:

```
**Q1** - **<question title>**: <question body>

Recommended: <your recommended answer>
```

Never invent a business reason. If the user has no answer, mark the gap as a pending line at the end of the card body.

## The HOW rule

Drop anything that describes how to implement or what was found before writing the card:

- file and folder paths
- plugin names
- class, function, and variable names
- event constants
- code snippets
- directory layout
- implementation steps

Keep a dropped item only when the user explicitly asks to include it. Presence in the source is not a request.

Keep what survives any implementation:

- product rules (the element appears after 3 seconds)
- a flag the developer must know (`isActive: true`)
- a tool name when the tool *is* the story (replace Cypress with Playwright)

Test: if the name only exists in the code and would vanish under a different implementation, it goes.

## Card format

Fixed sections, in this order. Headings follow the output language. Portuguese titles below are the canonical pattern; do not drift from them when the source is Portuguese.

1. `## Contexto` — why now, what hurts. One short paragraph.
2. `## Objetivo` — the outcome for the product or the person using it. One or two sentences.
3. `## Critérios de aceite` — 3–7 present-tense observable bullets. No Gherkin, no "the system shall". A criterion that can only be checked by reading code is HOW in disguise: drop it.

Optional, only when they earn their place:

- `## Fora de escopo` — whenever the source hints at what is out. Up to 5 items.
- `## Referências` — only links that already existed in the source. Never invent a URL.
- `## Subtasks` — only if the source lists them.
- Any other section that genuinely helps this card.

Use `##` headings (Jira Cloud converts them). No markdown tables (Jira leaves pipes literal). Rewrite the card title, keeping any prefix the source card already has. Optional: the team's card title prefixes are best configured in `AGENTS.md`; follow them when present, and never invent one. Output language matches the source language; translate section titles with it.

## Delivery

1. **Discard line** — first, only when something was actually cut. Categories and reason, no dumped content. Example: "Descartei nomes de arquivo, caminhos de pasta e constantes de evento, porque descrevem como fazer, não o que se espera do card." If nothing was cut, start with the rendered card.
2. **Rendered card** — title, then the body. Pendings are the last lines of the body.
3. **Approval to write** — Jira mode only. Never write right after drafting. Show the rendered card first, then always ask for approval to write it, stating where: update the source card or create a new one. To create, ask for the project if `AGENTS.md` does not define it. Write only after an explicit yes for this exact content; an approval never carries over to a redraft or another card. If the user asks for changes, redraft, show it again, and ask again. Send the body in the format the tool expects.
4. **Bloco (Copy & Paste)** — Markdown mode only. That heading, then one fenced markdown block in the Output reference shape, with title and body only. No issue type, no labels.

## Output reference

Shape only. Input can be anything; do not wait for a title or a card. In Markdown mode, this is the content of the Copy & Paste block.

```markdown
Documentar o plugin de Pause Ads para quem for mexer nele

## Contexto

O plugin de Pause Ads não tem documentação. Quem precisa entender quando o anúncio aparece, o que impede a exibição ou como ligar a feature acaba lendo o código.

## Objetivo

Quem abrir a documentação do plugin consegue explicar quando o Pause Ads aparece, por que ele não apareceu em um cenário específico e o que muda cada comportamento, sem precisar ler o código.

## Critérios de aceite

- A documentação descreve o encaixe do plugin no Player e aponta o que já está documentado no Adapter, sem repetir
- Há um fluxo da pausa do usuário até o anúncio aparecer, incluindo o delay de 3 segundos e o encerramento no play
- As regras que impedem a exibição estão listadas, inclusive as options `enablePauseAds` e `skipPauseAds`
- Os eventos de ciclo de vida e o essencial de configuração e teste local estão descritos
- O plugin aparece no índice de plugins do repositório

## Fora de escopo

- Página de Confluence para humanos
- Pause Ads em TVs e apps nativos
```
