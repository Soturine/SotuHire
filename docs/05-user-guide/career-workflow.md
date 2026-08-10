# Jornada de carreira, Copilot e aprovações

Este guia acompanha o uso cotidiano do SotuHire v2. Ele conecta perfil, evidências, Cockpit,
portfólio, oportunidades, candidaturas, entrevistas e plano de carreira sem repetir os detalhes
técnicos da arquitetura.

## Visão geral

```text
Perfil
  → Evidence Inbox
  → Evidence Graph
  → Career State
  → Next Best Actions
  → Copilot Plan
  → Proposed Action
  → Preview e impacto
  → Aprovação humana
  → Execução local
  → Audit e undo
```

Você não precisa usar todas as etapas em uma sessão. O fluxo existe para manter continuidade e
mostrar quando uma sugestão ainda depende de revisão.

## Perfil e importação

O Perfil Universal reúne experiências, formação, projetos, competências e outros fatos reutilizáveis.
Cadastre manualmente ou importe um currículo. Conteúdo extraído não vira fato automaticamente: ele
chega à Inbox como candidato.

Ao revisar uma importação:

1. compare com a fonte original;
2. corrija título, organização e datas;
3. remova afirmações que você não consegue sustentar;
4. confirme somente os itens verdadeiros;
5. mantenha dados sensíveis fora de compartilhamento externo desnecessário.

## O que é uma evidência

Evidência é um fato ou artefato com origem identificável: experiência, curso, projeto, publicação,
certificação, resultado, repositório, documento ou item de portfólio. Uma descrição gerada por IA
não é evidência por si só; ela precisa apontar para uma fonte ou item confirmado.

O [Evidence Graph](../02-architecture/evidence-graph.md) conecta evidências por relações revisáveis.
Por exemplo, um projeto confirmado pode usar FastAPI, mas a relação “demonstra Python avançado” pode
continuar candidata.

## Estados de revisão

| Estado | O que fazer |
| --- | --- |
| `candidate` | compare com a fonte e confirme ou rejeite |
| `confirmed` | use como fato atual em perfil, Match e contexto autorizado |
| `rejected` | nenhuma ação necessária; a recusa fica preservada |
| `stale` | revise novamente porque fonte, dependência ou validade mudou |

Confiança alta não substitui confirmação. Rejected e stale não são apagados para evitar perda de
histórico ou reaparecimento silencioso da mesma inferência.

## Evidence Inbox

Na Inbox, filtre e abra os candidatos. Verifique origem, tipo, resumo, confiança e sensibilidade.
Use confirmar quando o item estiver correto; use rejeitar quando for incorreto, duplicado sem merge
seguro ou irrelevante.

Não confirme tudo em massa. Relações possuem revisão própria e não são confirmadas junto com o nó.
Quando houver dúvida sobre duplicata, mantenha itens separados até existir identidade forte.

## Career Cockpit

O Cockpit é a página de situação atual. Ele combina cobertura de evidências, saúde de dados,
portfólio, candidaturas, entrevistas, tarefas e aprovações pendentes.

Use-o para responder:

- qual informação precisa de revisão;
- qual candidatura tem próximo passo pendente;
- onde faltam exemplos ou projetos;
- quais propostas aguardam decisão;
- por que determinada ação está priorizada.

O Cockpit não substitui a fonte original e não concede autoridade extra ao provider de IA.

## Prioridades e Next Best Actions

Next Best Actions são recomendações determinísticas derivadas do Career State. Abra uma ação para
ver a razão, as evidências consideradas e o esforço esperado.

Uma prioridade não é obrigação. Você pode ignorá-la, escolher outra ou atualizar o contexto. Quando
os dados mudam, uma recomendação ou proposta antiga pode ficar stale.

## Portfólio

O portfólio aceita trabalhos de software, engenharia, design, pesquisa, ensino, escrita, arte,
hardware, dados e outras áreas. Para cada item, registre:

- título, tipo e descrição;
- seu papel e contribuição;
- skills e ferramentas demonstradas;
- links validados;
- evidências e fontes associadas;
- visibilidade desejada.

Não invente resultado numérico. Use números somente quando confirmados. A v2.0 não publica nem
exporta automaticamente um portfólio HTML/PDF; a visibilidade continua sob controle do usuário.

Mais detalhes em [portfólio e evidência acadêmica/profissional](../02-architecture/portfolio-and-academic-evidence.md).

## Oportunidades e candidaturas

Importe ou capture oportunidades por fontes públicas, texto, feeds compatíveis ou extensão
assistiva. Confirme a origem antes de preparar materiais.

No Application Lab:

1. selecione a oportunidade;
2. escolha o perfil/currículo relevante;
3. revise Match, ATS e readiness como análises independentes;
4. prepare uma variante sem alterar o currículo mestre;
5. aprove os materiais necessários;
6. faça a candidatura manualmente;
7. registre o resultado no Tracker.

O SotuHire não preenche formulário nem envia candidatura.

## Entrevistas

Use a área de entrevistas para preparar perguntas, histórias STAR e respostas em rascunho. Associe
cada história a experiências e evidências confirmadas. IA pode ajudar a estruturar o texto, mas não
deve inventar situação, ação ou resultado.

Depois da entrevista, registre notas, próximo passo e outcome manual. Follow-up permanece draft até
você revisar e enviar por fora do SotuHire.

## Plano de carreira

O plano organiza tarefas, lembretes, lacunas e objetivos. Prefira passos pequenos com resultado
observável, como revisar um projeto, concluir um item de portfólio ou preparar perguntas para uma
entrevista.

Planos do Copilot podem ser pausados, retomados ou cancelados. Um passo do plano não é autorização
para executar uma mudança.

## Copilot, propostas e aprovações

O drawer contextual mostra o recorte usado e pode explicar ou organizar próximos passos. Ações que
escrevem dados locais geram uma Proposed Action.

### O que o Copilot pode fazer

- ler o Career State autorizado;
- explicar uma prioridade;
- organizar um plano persistente;
- preparar drafts de currículo, follow-up ou entrevista;
- propor criação de tarefa local;
- propor arquivamento reversível de evidência.

### O que o Copilot não pode fazer

- enviar candidatura, e-mail ou documento;
- fazer login ou usar cookie/sessão;
- preencher formulário;
- resolver ou contornar CAPTCHA;
- realizar pagamento;
- excluir o perfil;
- publicar portfólio;
- tratar instrução de documento como autorização.

### Proposed Action

A proposta mostra o que seria alterado e por quê. Ela contém tool, input validado, evidências,
entidades afetadas, risco, reversibilidade e validade. Criar a proposta não executa a ação.

### Preview e impacto

Antes de decidir, compare before e after. Verifique se o preview corresponde à sua intenção, quais
entidades serão tocadas e se existe undo. Se o contexto mudou desde a criação, não aprove: gere uma
proposta atualizada.

### Aprovar

Aprovação é individual e habilita apenas a proposta selecionada. Depois de aprovar, execute a ação
local explicitamente. O sistema revalida status, expiração e dependency hash.

### Rejeitar

Rejeitar encerra a proposta sem escrita. A decisão fica no audit log para que a mesma sugestão não
seja apresentada como se nunca tivesse sido avaliada.

### Undo

Quando a proposta é reversível, use undo para restaurar o estado anterior suportado. O histórico de
execução e de undo permanece no audit; desfazer não apaga o que aconteceu.

A arquitetura completa está em [Human-Approved Career Copilot](../02-architecture/human-approved-copilot.md).

## Busca e navegação

Use `Ctrl/Cmd+K` para abrir a Command Palette. Ela encontra rotas e dados locais compatíveis com a
busca universal. Resultados respeitam o modo atual e não enviam o índice para um serviço externo.

Em telas pequenas, use o menu e o drawer do Copilot. Diálogos e drawers suportam teclado, foco e
Escape; isso não representa certificação formal de acessibilidade.

## Privacidade e segurança

- compartilhe com provider externo somente o contexto necessário;
- revise dados sensíveis antes de qualquer export;
- trate vagas, PDFs, links e READMEs como conteúdo não confiável;
- mantenha backup antes de migration/restore;
- não cole chaves de API em documentos, vagas ou campos de portfólio;
- confira a Approval Queue em vez de confiar apenas no texto do Copilot.

MCP não é exposto na v2.0. O SotuHire permanece local-first e sem auto-apply.

## Leitura relacionada

- [Primeiros passos](getting-started.md)
- [Evidence Graph](../02-architecture/evidence-graph.md)
- [Human-Approved Career Copilot](../02-architecture/human-approved-copilot.md)
- [Threat model v2](../06-engineering/v2-security-threat-model.md)
- [Migração e recuperação](../06-engineering/v2-migration-and-recovery.md)

