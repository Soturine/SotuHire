# Primeiros passos no SotuHire v2

Este guia leva da instalação ao primeiro Career State útil. O SotuHire funciona localmente e pode
ser usado sem IA externa ou extensão.

## 1. Inicie o ambiente local

Siga as instruções do [README](../../README.md#instalação) para instalar o backend e o frontend. No
modo API Real, o navegador conversa com a FastAPI em loopback; no modo Demo, todos os dados são
fictícios e ficam claramente identificados.

Ao abrir o produto pela primeira vez:

1. escolha pt-BR ou en-US;
2. selecione tema claro, escuro ou do sistema;
3. leia a explicação local-first;
4. conclua o onboarding sobre perfil, evidências, IA opcional e aprovação humana.

## 2. Comece pelo Perfil Universal

O perfil reúne fatos profissionais e acadêmicos que podem ser reutilizados em currículo, Match,
portfólio e candidaturas. Você pode:

- cadastrar itens manualmente;
- importar texto ou currículo;
- importar dados acadêmicos compatíveis;
- revisar candidatos antes de confirmar.

Não é necessário preencher tudo. Comece por objetivo, experiências recentes, formação, projetos e
competências que você consegue sustentar com uma fonte ou exemplo.

## 3. Importe um currículo, se quiser

A importação aceita os formatos documentados no [Resume Studio](../02-architecture/resume-studio.md).
Extração não atualiza o perfil silenciosamente: os itens entram como candidatos para revisão.

Confirme apenas conteúdo correto. Corrija datas, títulos e descrições antes de usar o material em
uma candidatura.

## 4. Revise a Evidence Inbox

A Inbox separa informação capturada de fatos confirmados. Antes de abrir o Cockpit, revise os
candidatos mais importantes e observe:

- tipo de evidência;
- resumo;
- origem;
- confiança;
- possíveis duplicatas;
- marcação de dado sensível.

Os estados `candidate`, `confirmed`, `rejected` e `stale` são explicados no
[guia da jornada](career-workflow.md#estados-de-revisão).

## 5. Abra o Career Cockpit

Com algumas evidências confirmadas, o Cockpit resume cobertura, lacunas, candidaturas, entrevistas,
aprovações e Next Best Actions. Ele não produz um score único de “qualidade profissional”. Cada
prioridade mostra razão e sinais usados.

Use o Cockpit para escolher uma ação pequena e verificável: revisar evidência, completar um projeto,
preparar uma candidatura ou organizar um follow-up.

## 6. Use o Copilot com aprovação

O Copilot pode explicar o estado, organizar um plano e preparar propostas. Ele não pode enviar uma
candidatura, fazer login, resolver CAPTCHA, enviar e-mail ou publicar portfólio.

Quando houver escrita local:

```text
proposta → preview → impacto → aprovação → execução → audit → undo, quando suportado
```

Leia [Copilot, propostas e aprovações](career-workflow.md#copilot-propostas-e-aprovações) antes da
primeira execução.

## 7. IA e extensão são opcionais

O caminho determinístico local continua disponível sem Gemini, OpenAI, Ollama ou LM Studio. Um
provider pode ajudar com explicações e drafts, mas não confirma evidências nem controla regras.

A extensão 0.10.0 captura a página visível mediante ação do usuário. Ela não lê automaticamente
currículos locais e não habilita auto-apply. Consulte o [guia da extensão](../../browser-extension/README.md).

## 8. Privacidade básica

- dados de carreira começam locais;
- chaves de provider ficam no backend local;
- evidência sensível não entra em contexto externo por padrão;
- conteúdo importado passa por revisão;
- integrações externas exigem opt-in e finalidade compatível;
- backup deve ser feito antes de migração ou restore.

Detalhes: [privacidade do contexto](../04-ai/copilot-context-and-privacy.md) e
[threat model](../06-engineering/v2-security-threat-model.md).

## Próximo passo

Continue no [guia completo da jornada](career-workflow.md), que cobre Evidence Inbox, Cockpit,
portfólio, oportunidades, candidaturas, entrevistas, plano de carreira e Approval Queue.
