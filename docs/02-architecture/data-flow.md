# Fluxo de dados e arquitetura v2

A arquitetura v2 conecta ingestão, evidências, estado de carreira, propostas e execução local sem
entregar o source of truth a um provider de IA. O fluxo favorece dados tipados, revisão humana e
rastreabilidade em vez de automação implícita.

## Visão geral

```text
fontes e documentos
  → parsers/importadores
  → candidatos na Evidence Inbox
  → Evidence Graph revisado
  → Career State determinístico
  → Next Best Actions
  → plano e proposta do Copilot
  → aprovação humana
  → application service
  → SQLite, snapshots e audit
  → outcomes e novo Career State
```

## Camadas

### Interfaces

React Web, extensão e Local Companion são clientes. Eles apresentam dados e iniciam comandos, mas
não implementam regras autoritativas de Career State ou aprovação.

### API local

FastAPI expõe contratos `/api/v1` preservados e as superfícies `/api/v2` de evidence, portfolio,
Career State, approvals, Copilot, audit e search. Pairing, sessão e CSRF protegem mutações web no
modo API Real.

### Domínio

Parsers e módulos de carreira normalizam dados; Evidence Graph preserva proveniência e revisão;
Career State e NBA executam regras determinísticas; o Copilot cria planos e propostas usando um
registry fechado.

### Application services

Application services são a única passagem autorizada para efeitos locais. Eles recebem inputs já
validados e, para writes do Copilot, somente depois da approval boundary.

### Persistência

SQLite schema 8 é o writer dos domínios v2. Snapshots e audit preservam contexto de decisão. Stores
JSON/JSONL anteriores continuam onde existe compatibilidade legada, sem dual-write v2.

## Ingestão e revisão

PDF, DOCX, HTML, TXT, JSON Resume, Lattes, GitHub, feeds, páginas públicas e entrada manual têm
níveis diferentes de estrutura. Importadores convertem a fonte em schema conhecido e registram a
origem. Conteúdo novo começa como candidato quando exige confirmação.

O usuário revisa na Evidence Inbox. Confirmar libera o item como fato; rejeitar preserva a decisão;
stale indica que uma dependência precisa de nova validação.

## Career State e recomendações

Career State agrega dados locais confirmados e produz dependency hash. NBA ordena ações por regras
transparentes. Nenhum request de provider é necessário para calcular o estado oficial.

Snapshots de Career State são explícitos. Uma leitura comum do Cockpit não gera escrita oculta.

## Copilot e aprovação

O Copilot recebe intenção e contexto mínimo. Read-only pode responder diretamente; draft ou
write-local gera Proposed Action com preview, impacto, risco e evidências. O usuário aprova uma
proposta por vez. Antes da execução, expiry, dependency hash, status e idempotência são revalidados.

Detalhes em [Human-Approved Career Copilot](human-approved-copilot.md).

## Providers

O Provider Router oferece caminhos local, Gemini, OpenAI e endpoints locais compatíveis quando
configurados. Providers ajudam em extração, explicação e draft. Saída estruturada passa por schema e
fallback; falha externa não altera a regra determinística nem concede autoridade de tool.

Chaves ficam no backend local. Contexto externo é opt-in e omite conteúdo sensível por padrão.

## Outcomes e realimentação

Outcomes manuais de candidatura podem atualizar analytics e o próximo Career State. Eles não
recalibram pesos automaticamente nem transformam correlação em regra causal. O histórico anterior
permanece rastreável por snapshots e eventos.

## Source of truth por domínio

| Domínio | Source of truth atual |
| --- | --- |
| Evidence Graph | `evidence_nodes` e `evidence_edges` no SQLite |
| Portfólio v2 | `portfolio_items` no SQLite |
| Career State | derivado; snapshots explícitos no SQLite |
| Copilot | planos, steps, proposals, executions e audit no SQLite |
| Perfil/Tracker e módulos v1 | repositories existentes, com migração gradual documentada |
| Providers | configuração local; nunca source of truth de fatos |

## Boundaries de segurança

- interfaces não escrevem diretamente no banco;
- conteúdo importado é dado, não comando;
- schema rejeita campos desconhecidos;
- registry recusa tool não allowlisted;
- writes exigem approval quando aplicável;
- stale e expiry são verificados na execução;
- audit é append-oriented e undo não apaga o evento original;
- auto-apply, login, CAPTCHA, pagamento e envio automático continuam fora do produto.

## Exemplo de fluxo

```text
1. Usuário importa currículo.
2. Parser cria candidato "Projeto Aurora" com source_ref do documento.
3. Usuário confirma o projeto e rejeita uma skill incorreta.
4. Career State identifica portfólio incompleto.
5. NBA sugere revisar o projeto.
6. Copilot propõe criar uma tarefa local.
7. Usuário revisa preview e aprova.
8. Application service cria a tarefa de modo idempotente.
9. Audit registra proposta, aprovação e execução.
10. Novo Career State passa a considerar a tarefa pendente.
```

## Trade-offs

SQLite simplifica operação local e recuperação, mas não oferece visualização de graph pronta como
um produto especializado. Aprovação adiciona um passo à jornada, porém reduz execução equivocada e
torna o sistema demonstrável. Manter compatibilidade v1 evita migração destrutiva, ao custo de uma
transição gradual de stores legados.

## Links relacionados

- [Evidence Graph](evidence-graph.md)
- [Human-Approved Career Copilot](human-approved-copilot.md)
- [Mapa de integração](module-integration-map.md)
- [Schema SQLite e migrações](sqlite-schema-and-migrations.md)
- [Threat model v2](../06-engineering/v2-security-threat-model.md)
- [Migração e recuperação v2](../06-engineering/v2-migration-and-recovery.md)
