# Human-Approved Career Copilot

O Human-Approved Career Copilot coordena informações e ações de carreira sem assumir autoridade
sobre decisões do usuário. Ele observa um estado determinístico, explica prioridades, cria planos e
propõe alterações. Uma proposta só atravessa a fronteira de escrita depois de revisão e aprovação
humana individual.

Este documento centraliza Career State, Next Best Actions, planos, Tool Registry, Proposed Actions,
Approval Queue, execução, undo, auditoria e a decisão de não expor MCP na v2.0.

## Problema arquitetural

Um assistente que lê currículo, vagas e documentos pode produzir sugestões úteis, mas esses dados
também podem estar incompletos, desatualizados ou conter instruções maliciosas. Permitir que o mesmo
componente interprete conteúdo e execute ações criaria uma boundary fraca.

O SotuHire separa três responsabilidades:

1. regras determinísticas calculam estado e prioridades;
2. o Copilot planeja, explica e cria propostas tipadas;
3. application services executam apenas propostas aprovadas e ainda válidas.

O modelo de IA, quando usado, não controla regras de negócio, não confirma evidências e não recebe
autoridade de tool.

## Fluxo ponta a ponta

```text
Career State
    ↓
Next Best Actions
    ↓
Copilot Plan
    ↓
Proposed Action
    ↓
Preview + Impact + Risk
    ↓
Human Approval
    ↓
Application Service
    ↓
Audit
    ↓
Undo, quando suportado
```

Rejeição, expiração ou stale encerram o caminho antes da execução. Não existe “aprovar tudo”.

## Career State

`CareerStateEngine` agrega dados locais de maneira determinística. Evidências confirmadas, graph,
portfólio, oportunidades, candidaturas, entrevistas, follow-ups, tarefas vencidas e outcomes
participam do estado. O resultado possui `dependency_hash`, permitindo detectar se uma recomendação
ou proposta foi construída sobre uma visão que já mudou.

O estado separa:

- cobertura: quanto do contexto necessário está disponível;
- confiança de regra: força das condições determinísticas aplicadas;
- confiança de provider: qualidade declarada de uma explicação externa, quando houver.

Não há um score mágico que substitua essas dimensões. Renderizar o Cockpit é read-only; snapshots
são gravados apenas quando solicitados explicitamente.

## Next Best Actions

O Next Best Action Engine transforma o Career State em candidatos priorizados por regras
transparentes. Exemplos incluem revisar evidência pendente, preencher uma lacuna de portfólio,
preparar candidatura, revisar follow-up ou atualizar um documento stale.

Cada candidato carrega razão, referências e sinais de prioridade. IA pode explicar a recomendação,
mas não recalcular o estado nem alterar pesos com base em outcome de forma automática.

## Copilot Plans

Um plano organiza uma intenção em passos persistentes. Na v2.0, planos podem ficar `active`, ser
pausados, retomados ou cancelados. A persistência permite continuar o trabalho sem tratar uma
conversa efêmera como source of truth.

Passos do plano descrevem trabalho possível; eles não são execuções. Um `proposal_id` só aparece
quando uma ação concreta é preparada pelo fluxo autorizado. Texto de vaga, PDF ou README nunca
pode criar essa autorização sozinho.

## Categorias de tools

O registry interno distingue capacidades por efeito:

| Categoria | Exemplo | Aprovação |
| --- | --- | --- |
| `read-only` | ler Career State ou contexto permitido | pode executar sem escrita |
| `draft` | preparar currículo, follow-up ou resposta de entrevista | gera conteúdo revisável; não envia |
| `write-local` | criar tarefa ou arquivar evidência reversivelmente | exige Proposed Action e aprovação |
| proibida | submit, send email, login, CAPTCHA, pagamento, sessão, delete profile | não existe no registry |

Draft não é sinônimo de envio. Um rascunho pode ser salvo ou revisado localmente, mas não dispara
comunicação externa.

## Tool Registry

Cada tool allowlisted declara:

- ID e descrição;
- schema estrito de entrada e contrato de saída;
- domínio e categoria;
- `read_only` e `requires_approval`;
- nível de risco;
- handler autorizado.

O registry recusa IDs desconhecidos e impede write sem `requires_approval=true`. Campos extras no
input são rejeitados; assim, um payload não pode esconder `submit_automatically` em uma operação de
criação de tarefa.

O registry é uma boundary de segurança, não um catálogo gerado pelo provider. Prompts e documentos
não adicionam tools.

## Proposed Action

Uma Proposed Action é um pedido de mudança, não a mudança em si. Ela registra:

- tool e input validados;
- motivo e evidências consideradas;
- entidades afetadas;
- snapshot anterior e preview posterior;
- impacto e risco;
- reversibilidade e estratégia de undo;
- dependency hash, expiração e idempotency key;
- status do lifecycle.

Criar a proposta não executa o handler. Essa separação torna a intenção inspecionável e testável.

## Preview e impacto

O preview mostra o resultado esperado antes da escrita. Para uma tarefa, por exemplo, inclui título,
tipo, prioridade e prazo; para arquivamento, mostra a mudança de review status. O impacto descreve
entidades tocadas e possíveis consumidores afetados.

O preview não é uma simulação ilimitada do mundo externo. Ele representa apenas o efeito local que
o application service conhece e pode validar.

## Approval Queue

A Approval Queue reúne propostas pendentes. Cada card deve mostrar razão, evidence refs, before e
after, impacto, risco, expiração, reversibilidade e undo strategy.

A aprovação é individual. Aprovar habilita a próxima transição, mas não cria uma permissão global
para o Copilot. Rejeitar preserva a decisão no audit log e impede execução posterior daquela
proposta.

Transições usam compare-and-set. Isso evita que duas abas ou requests concorrentes executem a mesma
ação em estados incompatíveis.

## Approval boundary

Somente status `approved` pode chegar ao executor. Antes de executar, o sistema verifica novamente:

- schema e tool allowlisted;
- ownership e status esperado;
- expiração;
- dependency hash;
- idempotency key;
- estratégia de undo para ações marcadas como reversíveis.

Se o Career State mudou desde o preview, a proposta vira `stale`. O usuário precisa gerar e revisar
uma proposta nova; a aprovação anterior não é reaproveitada.

## Execução

O executor chama um application service local depois da aprovação. Ele não entrega ao modelo acesso
direto ao SQLite, filesystem ou browser. O resultado da execução e os snapshots relevantes são
registrados separadamente da proposta.

Idempotência evita efeitos duplicados em retries. Repetir a mesma intenção enquanto a proposta
compatível ainda existe retorna o mesmo identificador em vez de multiplicar ações.

## Undo

Ações reversíveis precisam declarar uma estratégia executável antes de serem propostas. Undo usa o
snapshot anterior para restaurar o estado suportado, mas não apaga o evento original. Executar e
desfazer são dois fatos do histórico.

Nem toda ação seria reversível no mundo externo; por isso tools de submit, e-mail ou pagamento não
fazem parte da v2.0. O undo existente se limita a efeitos locais que o SotuHire controla.

## Audit

O audit log registra ator, evento, proposta, referências, motivo, before, after, payload sanitizado e
timestamp. Ele permite responder quem aprovou, o que foi executado e se houve undo.

Audit não é chain-of-thought. Explicações mostram regra, evidência, confiança e decisão de produto,
sem expor raciocínio interno de modelo ou segredo de provider.

## Contexto e privacidade

O Copilot seleciona o menor contexto necessário para o propósito. Context receipts registram
quantidade de itens, estimativa de tokens, compartilhamento externo e itens sensíveis omitidos.

Evidência não confirmada ou sensível não entra automaticamente em prompt externo. Chaves de
provider permanecem no backend local e nunca fazem parte de proposta, audit ou export.

## Prompt injection

Vaga, PDF, currículo, README, RSS, link e item de portfólio são dados não confiáveis. Instruções
dentro desses conteúdos não alteram o registry, não aprovam propostas e não invocam handlers.

A defesa é estrutural:

```text
conteúdo não confiável
  → parsing/schema
  → candidate ou contexto limitado
  → plano/proposta tipada
  → aprovação humana
  → application service
```

## MCP futuro

**MCP não é exposto na v2.0.** O registry interno já separa read-only, draft e write-local, mas isso
não equivale a disponibilizar um servidor MCP.

Uma exposição futura só deve ser considerada com transporte loopback, enable explícito, token,
scopes, ownership e audit testados de ponta a ponta. Scopes para submit, e-mail, login, cookies,
sessão, CAPTCHA, pagamento ou delete profile não devem existir.

Manter esta decisão no documento central evita criar uma página extensa para uma feature que ainda
não faz parte do produto.

## Source of truth

Planos, propostas, execuções, snapshots, audit e dados do graph usam SQLite schema 8 nos domínios
v2. JSON/JSONL legado permanece apenas onde há compatibilidade ou export explícito. Não existe
dual-write v2 para stores paralelos.

Career State é derivado dos dados persistidos; não é um store autoritativo editado por IA. O
provider pode produzir explicação ou draft, nunca o valor oficial das regras.

## Invariantes

1. Inferência não vira evidência confirmada sem revisão.
2. Plano não é execução.
3. Proposta não é aprovação.
4. Aprovação não ignora stale, expiry ou schema.
5. Provider não controla tools nem regras determinísticas.
6. Conteúdo importado nunca autoriza ação.
7. Undo preserva audit.
8. Ações externas críticas permanecem fora do registry.

## Exemplo

```text
Career State: portfólio sem projeto confirmado recente
Next Best Action: revisar Projeto Aurora
Plan step: verificar evidências do projeto
Proposal: criar tarefa local "Revisar Projeto Aurora"
Preview: nova tarefa, prioridade medium, sem envio externo
Human approval: usuário aprova individualmente
Execution: application service cria a tarefa de forma idempotente
Audit: proposal_approved + execution_succeeded
Undo: remove a tarefa criada e registra proposal_undone
```

## Limites da v2.0

- não há auto-apply;
- não há envio automático de mensagens ou documentos;
- não há form filling, login, cookies ou bypass de CAPTCHA;
- não há MCP exposto;
- IA continua opcional;
- o Copilot não substitui julgamento profissional, jurídico ou regulatório.

## Links relacionados

- [Evidence Graph](evidence-graph.md)
- [Fluxo de dados v2](data-flow.md)
- [Contexto e privacidade do Copilot](../04-ai/copilot-context-and-privacy.md)
- [Threat model v2](../06-engineering/v2-security-threat-model.md)
- [Guia da jornada e aprovações](../05-user-guide/career-workflow.md)
