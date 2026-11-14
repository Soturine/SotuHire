# Dogfood bidirecional e pesquisa externa — 2026-11

Parte da [auditoria independente de 2026-11](2026-11-independent-assurance-audit.md). Registra o
que as ferramentas de assurance acharam no SotuHire, o que deixaram passar, o que o SotuHire
ensinou a elas e o que foi corrigido em cada repositório dono.

## O que cada ferramenta viu

| Pergunta | Derivanta Engine 0.1.0 | Assertiva 1.0.0 | Agente |
| --- | --- | --- | --- |
| Approval revalidado no efeito? (SH-AUD-001/002/003) | fora do escopo (estático) | não detectou | reproduzido com testes |
| Tarefa do Copilot quebra a lista de tarefas? (SH-NEW-002) | não | não (o teste de API existente executava e desfazia, mas nunca listava) | reproduzido |
| SBOM órfão no CI (SH-AUD-006) | **não**: inventariou 3 workflows e leu 0 | parcial: `ARTIFACT_LINEAGE_UNKNOWN` (genérico) | lido no workflow |
| `npm audit` não bloqueante com crítica no lock | não | não | `npm audit` |
| Funções não referenciadas | 36 candidatos, todos com uma única ocorrência (precisão do sinal: 36/36) | — | 6 removidas após checar uso dinâmico e superação |
| Testes que não checam estado após rejeição | — | `STATE_AFTER_REJECTION_NOT_EVIDENCED`, inclui `test_changed_career_state_marks_proposal_stale` (verdadeiro: não checava que nenhuma tarefa foi criada) | confirmado |
| Hooks pre-commit fora do CI | — | `LOCAL_CHECK_NOT_OBSERVED_IN_CI` (alta) | **falso positivo**: o CI roda `ruff check .` e `ruff format --check .` |
| Wheel construído funciona? | — | `ARTIFACT_QUALIFICATION_FAILED` (alta) | causa: build não-isolado sem `wheel` no interpretador; a mudança no projeto removeu a dependência e o wheel foi qualificado à mão |

Execuções (relatórios brutos fora do repositório; SHA-256 de cada um abaixo):

- `derivanta-engine inspect <git archive de 8ea37d7> --maintainability --format json` → 1.509
  arquivos, 602 Python, 271 candidatos (36 não referenciados, 18 corpos duplicados, 152 tabelas
  repetidas, 65 de alta complexidade), `inventory_complete: true`.
- `assertiva audit <worktree> --execute --dependencies` em `8ea37d7` (661 passed) e em `ad04b23`
  (685 passed), 13 findings em ambos, nenhum ligado aos defeitos de integridade.
- `derivanta-engine inspect` (branch `feat/ci-workflow-checks`) em worktrees de `8ea37d7` e da
  branch de correção.

| Relatório | SHA-256 |
| --- | --- |
| Engine inspect, `8ea37d7` | `5f767b1d519e84a2abc2db37df1010a936ca241e0d7844cede00927532d2919a` |
| Engine CI checks, `8ea37d7` | `23ec9b1241054d134e49c1320cff759abc94f25b2610be9d9b9f7db99052bd82` |
| Engine CI checks, branch | `43267d2ab637fb18d5560a8a87f2e72d42caeddd4fdaa78b168230d1a3a2344b` |
| Assertiva audit, `8ea37d7` | `70ae1b6a0bf48bca637b3dd4199f74d77aa59612f7c804d71a88dea8635e568e` |
| Assertiva audit, `ad04b23` | `b1a198b40c620b9e0ceb1cab20edfaa5de4a87a189535e875093c488f7694323` |
| Controles negativos M1–M10 | `712377c508aca00092705d1a5cafb13ef66dc6e5e79967549d104e49969c8dbc` |
| Harness da extensão, `8ea37d7` | `ce7e35fdeb07fa70de844a349c16f913db37723ba746c3155056946b8efd1955` |
| Harness da extensão, branch | `b1ff8db623dd9e983cd150b196da847e26d70460b7d7bb18d8c877b918c6e659` |

## Correções nas ferramentas (repositórios donos, branches locais)

| Dono | Branch | Mudança | Evidência |
| --- | --- | --- | --- |
| Derivanta (Framework) | `feat/approval-consumption-and-required-artifacts` | `security/AI_AGENT_SECURITY.md`: "Approval consumption at the point of effect" (revalidar e consumir a aprovação atomicamente com o efeito, undo condicional, testes que provam). `checklists/RELEASE.md`: artefato obrigatório falha quando falta, nome derivado do manifest, escopo do SBOM declarado e verificado, audit `continue-on-error` não é gate. | `scripts/tests` 26 passed; checks de links/estrutura com a mesma saída antes e depois (4 e 54 itens pré-existentes) |
| Derivanta Engine | `feat/ci-workflow-checks` | `core/ci_workflows.py` (puro): `ENG-CI-ARTIFACT-OPTIONAL` e `ENG-CI-NONBLOCKING-AUDIT`; leitura limitada no `service`. | suíte própria 951 passed; no SotuHire: `8ea37d7` → 4 candidatos, 4 verdadeiros; HEAD → 1 (o relatório "high" mantido não-bloqueante por política, `ACCEPTED_RISK`) |
| Assertiva | `fix/precommit-hook-tool-identity` | hooks remotos conhecidos (`ruff-pre-commit`: `ruff`, `ruff-check`, `ruff-format`) mapeados para a ferramenta que rodam, só para aquele repositório; limitação registra que o comando foi inferido. | `tests/test_pre_commit_known_hooks.py`: 3 falham sem o patch, 4 passam com ele |

As próprias regras de arquitetura do Engine pegaram meu primeiro patch (I/O dentro de `core`,
regra fora do catálogo de rastreabilidade, módulo fora do mapa de arquitetura) — o dogfood também
validou os gates do Engine.

Nada disso foi publicado: as branches existem só localmente e não há tag nem release.

## Lacunas das ferramentas ainda abertas

- **Assertiva**: classifica como `FAIL` de projeto um build que falhou por dependência do
  backend ausente no interpretador usado pelo auditor; deveria ser `BLOCKED_ENVIRONMENT`.
- **Assertiva**: não tem sinal para "transição de ciclo de vida não exercitada" (aprovar → mudar
  dependência → executar). Os defeitos P0 desta auditoria passaram por todos os sinais estáticos.
- **Engine**: o sinal de não-referenciado é preciso, mas é só Python; consumidores TS/JS de
  endpoints e o mesmo para duplicação cross-language ficam invisíveis.
- **Engine**: 152 `DUPLICATE_TABLE` com custo de triagem alto e valor baixo no SotuHire (tabelas de
  strings de i18n e de domínio); falta um agrupamento por arquivo/propósito.
- **Ambiente**: `PIP_NO_BUILD_ISOLATION=0` desativa o isolamento do pip (o nome engana); quebra
  installs editáveis de Engine e Assertiva sem `hatchling`/`editables` no ambiente.

## Pesquisa externa

Consultado em 2026-11-14. "Observado" é o que a fonte primária mostra; não houve uso dos produtos.

| Referência | Observado | Para o SotuHire | Decisão |
| --- | --- | --- | --- |
| [OWASP AI Agent Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html) | "Check and consume the approval in one atomic step immediately before execution"; aprovação ligada à chamada exata; autorização fora do contexto do agente | É exatamente o defeito SH-AUD-001/002 | `ADOPT` (implementado) |
| [Chrome extensions — Stay secure](https://developer.chrome.com/docs/extensions/develop/security-privacy/stay-secure) | Mensagens de content script podem ser forjadas; validar o `MessageSender` mesmo em `runtime.onMessage`; content scripts não devem pedir URLs arbitrárias | É o SH-NEW-007 | `ADOPT` (implementado) |
| [career-ops](https://github.com/career-ops-hq/career-ops) | Agente local em CLIs de IA, MIT; Markdown/YAML locais; nota 1–5 por vaga (A–H) incluindo legitimidade da vaga; preenche mas nunca envia; tracker com cadência de follow-up e análise de padrões de rejeição | Concorrente conceitual mais próximo; o SotuHire diferencia por evidência confirmada, aprovação por ação e undo | `ADAPT`: checagem de legitimidade da vaga e análise de padrões de rejeição como NBAs determinísticas |
| [Reactive Resume](https://github.com/amruthpillai/reactive-resume) | MIT, React 19 + TanStack Router + Vite, PostgreSQL, exporta PDF/DOCX/Markdown/JSON, importa JSON Resume, IA opcional com aceitar/rejeitar por edição | Stack de frontend parecida; IA como proposta revisável, como no SotuHire | `ADAPT`: import/export JSON Resume; `REJECT` PostgreSQL (o SQLite local-first é proporcional) |

Conclusão: nenhuma referência justifica trocar a stack. O diferencial defensável do SotuHire é a
fronteira de aprovação com evidência e undo — que só agora está de fato garantida no efeito.
