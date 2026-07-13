# Snapshots de vaga, currículo, análise e edital

## Por que snapshots

Vagas e editais podem mudar ou desaparecer; currículos e análises também evoluem. O cartão mutável do Tracker não é suficiente para responder qual conteúdo existia no momento da análise ou candidatura.

`modules/storage/snapshots.py` preserva cópias imutáveis no SQLite e `modules/storage/applications.py` mantém os vínculos da candidatura.

```text
JobSnapshot ──────────────┐
                         ├─ AnalysisSnapshot ─┐
ResumeSnapshot ──────────┘                    │
                                              ├─ ApplicationRecord
Tailored ResumeSnapshot ──────────────────────┤
PublicExamSnapshot (histórico separado)       │
Capture ──────────────────────────────────────┘
```

## Modelo de imutabilidade

A proteção existe em dois níveis:

1. os modelos Pydantic são `frozen=True`;
2. triggers SQLite rejeitam `UPDATE` e `DELETE` nas quatro tabelas de snapshot.

O hash SHA-256 é calculado sobre JSON canônico com chaves ordenadas. `snapshot_id`, `content_hash` e timestamps de criação/captura não entram no hash. Assim, repetir o mesmo conteúdo no mesmo escopo reutiliza o snapshot; alterar conteúdo cria outro ID/hash.

## `JobSnapshot`

| Campo | Uso |
|---|---|
| `snapshot_id` | identidade imutável |
| `opportunity_id` | vínculo opcional com a oportunidade/cartão |
| `title`, `organization`, `location` | metadados exibíveis |
| `description`, `raw_text` | cópia do conteúdo disponível |
| `source_url`, `source_refs` | proveniência |
| `captured_at` | instante da captura |
| `content_hash` | identidade por conteúdo |
| `source_kind` | método/origem da coleta |
| `structured_data` | requisitos e demais campos estruturados |

O escopo de dedupe é oportunidade + hash. Se `opportunity_id` não existir ainda, `SnapshotStore` cria uma linha mínima em `opportunities` para satisfazer a FK.

## `ResumeSnapshot`

| Campo | Uso |
|---|---|
| `snapshot_id` | identidade imutável |
| `profile_id` | Perfil Universal de origem, quando conhecido |
| `resume_variant_id` | currículo mestre ou variante |
| `title`, `content` | nome e conteúdo efetivamente usados |
| `structured_sections` | seções estruturadas, quando disponíveis |
| `source_profile_item_ids` | evidências do Perfil que compõem a versão |
| `created_at`, `content_hash` | tempo e identidade do conteúdo |

O escopo de dedupe é perfil + variante + hash. Um perfil mínimo é criado quando o ID informado ainda não existe.

## `AnalysisSnapshot`

Preserva:

- `analysis_type`;
- IDs da vaga e do currículo usados;
- provider/modelo solicitado e usado;
- `prompt_id` e `prompt_version`;
- `fallback_used`;
- resultado estruturado;
- `evidence_used` e `source_refs`;
- tempo e hash.

O conteúdo não inclui chave de API. O `SnapshotStore` procura uma análise existente por tipo + vaga + currículo + hash. Como essa combinação ainda não possui restrição `UNIQUE` no schema, a proteção contra corrida entre processos é limitada à consulta realizada antes do insert.

## `PublicExamSnapshot`

Preserva o estado do edital e, quando aplicável, de um cargo:

- `notice_id` e `role_id`;
- `raw_text`;
- `structured_notice`;
- requisitos;
- cronograma;
- `captured_at` e `content_hash`.

Ao salvar um `ExamNotice`, o store cria um snapshot geral e outro para cada cargo. Apagar o edital do store revisável JSON não remove o histórico imutável.

## Tracker: cartão mutável e evidência imutável

`StoredAnalysis` continua sendo o cartão de uso diário. Ele possui:

```text
job_snapshot_id
resume_snapshot_id
tailored_resume_snapshot_id
match_analysis_snapshot_id
ats_analysis_snapshot_id
source_capture_id
applied_at
stage_history
contact_history
interview_notes
follow_up_at
outcome
outcome_reason
```

`JobTracker._persist_reliable_state()` cria ou reutiliza:

1. `JobSnapshot`;
2. `ResumeSnapshot`, somente quando o texto do currículo foi fornecido;
3. análise de Match;
4. análise ATS;
5. variante ajustada, quando há resultado de Tailor;
6. `ApplicationRecord` com todos os vínculos.

`ApplicationRepository.save()` cria um `application_event` quando a etapa é nova ou muda.

### Modo rápido

Cargo, organização, URL e status continuam suficientes. Nesse caso, o `JobSnapshot` preserva os metadados, requisitos e notas disponíveis; `raw_text` pode permanecer vazio se o anúncio não foi fornecido. O sistema não inventa a descrição ausente e não cria `ResumeSnapshot` sem conteúdo de currículo.

### Modo completo

Quando vaga, currículo, variante, captura e trace estão disponíveis, a candidatura fica ligada ao anúncio, ao currículo e às análises realmente usados. Esse é o modo que preserva uma cópia completa mesmo se a página original sair do ar.

## Capturas da extensão

A Local Companion:

- cria `JobSnapshot` ao receber uma captura de vaga;
- cria `PublicExamSnapshot` ao receber uma captura de edital;
- mantém `snapshot_id`, `snapshot_history` e `content_hash` no registro de captura;
- cria `ResumeSnapshot` para o contexto usado na análise, quando ele existe;
- cria `AnalysisSnapshot` para a análise da captura;
- encaminha o `source_capture_id` ao Tracker.

O snapshot contém apenas o payload sanitizado entregue pela extensão. Cookies, tokens, sessão, headers autenticados e storage de terceiros não fazem parte desse fluxo.

## Consistência e limites

- snapshots não são editados; correções geram nova versão;
- uma entidade de origem não pode ser removida enquanto estiver referenciada por snapshot; uma política futura de retenção deve tratar esse vínculo explicitamente;
- um snapshot referenciado por candidatura/análise não pode ser removido;
- o Tracker ainda grava o cartão JSON e o espelho SQLite em etapas separadas; não existe transação única entre arquivo e banco;
- dados legados sem texto original permanecem com vínculo incompleto e geram warning no health check;
- `SnapshotStore` expõe atualmente leitura direta de `JobSnapshot`; consultas adicionais podem ser adicionadas conforme as telas passarem a exibir históricos completos.

## Testes

```bash
pytest tests/test_storage_snapshots.py
pytest tests/test_storage_migrations.py
pytest tests/test_job_tracker.py
pytest tests/test_extension_capture_flow.py
```

Os testes confirmam reutilização por conteúdo, novo hash quando o texto muda, vínculo da candidatura e rejeição de mutação no banco.
