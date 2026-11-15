# Mapa de autoridade dos dados profissionais — 2026-11

Parte da [auditoria de 2026-11](2026-11-independent-assurance-audit.md) (CP-DATA01). Responde: depois
de informar ou importar um fato no Perfil, a pessoa precisa digitá-lo de novo em outra tela? Cada linha
diz onde o dado mora, quem escreve, quem lê e se a leitura é projeção (lida do dono na hora) ou cópia.
"Verificado" quer dizer lido no código e coberto por teste nesta revisão.

## Fronteiras

```text
Perfil Universal  ──(projeção, só fatos confirmados e não sensíveis)──▶  Currículo Mestre
   (fonte da verdade)                                                     (documento editável)
        ▲                                                                        │
        │ nunca escreve de volta                                         (cópia por vaga)
        │                                                                        ▼
        └──────────────────────────────── Variante por vaga ◀───────── Application Lab
```

- O **Perfil** é dono dos fatos e da confirmação (`review_status`/`confirmed_by_user`, regra única em
  `modules/evidence.reconcile_review_status`).
- O **Currículo Mestre** é derivado do Perfil (`modules/application_lab/profile_projection.py`) e
  editável; cada entrada guarda `source_profile_item_ids`.
- A **variante** é uma cópia do Mestre para uma vaga; editar a variante não muda o Mestre nem o Perfil
  (teste `test_later_profile_facts_reach_the_resume_only_after_review_and_never_flow_back`).
- O **rascunho local** (`localStorage`) só cobre um salvamento interrompido e nunca substitui conteúdo
  mais novo do servidor (`apps/web/src/features/resume-studio/draft.ts`).

## Entidades

| Entidade | Mora em | Escreve | Lê | Tipo |
| --- | --- | --- | --- | --- |
| Identidade, resumo, cargos-alvo, preferências | Perfil (`UniversalCareerProfileStore`, JSON local) | `/api/v1/profile` (PUT), importações | Mestre (projeção na criação), contexto de carreira, extensão (`profile_summary` no handshake) | fonte da verdade |
| Experiências, formação, projetos, certificações, competências, idiomas, publicações | itens do Perfil | `/api/v1/profile/items`, Lattes, JSON Resume, captura | Mestre (projeção revisável), Match/ATS/Readiness via contexto | fonte da verdade |
| Currículo Mestre | SQLite (`ApplicationLabRepository`) | `/resume-studio/master/from-profile` (novo), `/resume-studio/ingest` + PUT, `/master/profile-updates` (novo) | Resume Studio, Application Lab, exportações | derivado editável |
| Variante por vaga | SQLite | Resume Studio (autosave), Application Lab | exportação PDF/DOCX/JSON Resume | cópia por vaga |
| Rascunho do Resume Studio | `localStorage` `sotuhire:resume-draft:<master>` | autosave no navegador | Resume Studio ao abrir, só se for da mesma variante e mais novo | rascunho |
| Evidências e grafo | SQLite (Copilot v2) | revisão humana, Copilot com aprovação | Career State, NBAs | fonte da verdade |
| Oportunidades, Radar, Tracker | `LocalStore` (JSON) e SQLite (`applications`) | captura, Radar, Tracker | Application Lab, Tracker | compatibilidade + canônico (ver [arquitetura de storage](../02-architecture/storage-repository-architecture.md)) |

## O que foi corrigido neste checkpoint

| Problema verificado | Antes | Depois | Prova |
| --- | --- | --- | --- |
| Perfil → currículo exigia nova digitação | sem Mestre, o Resume Studio só oferecia importar um arquivo de novo | `POST /resume-studio/master/from-profile` monta o Mestre com os fatos confirmados | `tests/test_profile_to_master_resume.py`, E2E `resume-studio-profile.spec.ts` |
| Primeiro uso sem saída | a API respondia 404 e a tela mostrava erro com "tentar novamente" (o modo demo escondia, porque sempre devolve um Mestre) | 404 vira a tela "Seu Currículo Mestre ainda não existe" com as duas opções | E2E falha com a rota anterior (controle negativo) |
| Fatos novos do Perfil não chegavam ao currículo | divergência silenciosa | lista de fatos confirmados ausentes do Mestre; a pessoa escolhe quais entram; nada muda sozinho | testes de API (422 para não confirmado, sensível ou inexistente) e E2E |
| Rascunho velho vencia o servidor | qualquer rascunho no navegador substituía a variante salva, e nunca era apagado | vence só se for da mesma variante e mais novo; é apagado ao salvar | `draft.test.ts` (4 casos) |
| Terceira cópia da regra de confirmação | `ResumeEntry` repetia a regra | usa `reconcile_review_status` | suíte Python |

Campos que deixam de ser redigitados ao criar o Mestre a partir do Perfil: resumo, cargo-alvo e, por
item confirmado, título, organização/instituição, descrição e datas, nas seções de experiência,
formação, projetos, certificações e registros, competências, idiomas, publicações, prêmios,
voluntariado e interesses.

## Em aberto

- ~~Fatos editados no Perfil depois de projetados não atualizam a entrada no Mestre.~~ Resolvido no
  CP-UX02 (seção abaixo): a diferença é listada com antes/depois e aplicada só a pedido.
- `LocalStore` ainda é usado por Application Lab, Local API, Radar, fontes e Tracker; a retirada segue
  a política de migração com backup e rollback e não foi feita neste ciclo.
- ~~Variantes em "última gravação vence".~~ Resolvido no CP-UX02 (seção abaixo).
- Reimportar o mesmo arquivo gera o mesmo `master_resume_id` (`master-{hash}`) e a adoção do rascunho
  é um upsert sem versão: substitui fatos aplicados do Perfil a esse Mestre. Ficou assim para não
  quebrar a reimportação; a tela de importação ainda não avisa.

## Concorrência e idempotência do Currículo Mestre (CP-SEC02)

| Caso | Antes | Depois | Prova |
| --- | --- | --- | --- |
| Mesmo ID repetido no pedido de aplicar fatos | uma entrada por repetição (a checagem deduplicava, a montagem iterava a lista original) | uma entrada | `test_a_repeated_id_adds_the_fact_once` (3 entradas → 1) |
| Retry de um pedido que já deu certo | 422 "já presentes" | 200 com o mesmo currículo, sem gravar | `test_a_retried_request_answers_200_with_the_same_resume` |
| Duas gravações a partir da mesma cópia | a segunda apagava a primeira | a segunda recebe 409; a primeira fica | `test_a_write_based_on_a_stale_copy_is_refused`, `test_the_api_maps_a_stale_write_to_409`, `test_put_with_an_old_expected_version_answers_409_and_keeps_the_newer_copy` |

O token de versão é o `updated_at` do Mestre; a conferência e a gravação ficam na mesma transação
`BEGIN IMMEDIATE`, então dois escritores não passam os dois pela conferência. Os testes foram rodados
contra o código anterior primeiro: 5 dos 6 falharam.

## Variantes e fatos alterados no Perfil (CP-UX02)

| Caso | Antes | Depois | Prova |
| --- | --- | --- | --- |
| Duas abas editando a mesma variante | o autosave da segunda apagava a primeira, sem aviso | `PATCH` com `expected_updated_at`; 409 se a versão salva mudou; o editor para o autosave e pergunta "Carregar a versão salva" ou "Manter a minha" (esta grava sem versão, por escolha) | `test_a_variant_patch_from_a_stale_copy_answers_409_and_keeps_the_newer`, `test_conditional_variant_writes_cannot_both_win`, E2E `a variant saved elsewhere stops autosave…` e `loading the saved version…` |
| Fato editado no Perfil depois de entrar no Mestre | o Mestre ficava com o texto antigo, sem sinal | `GET /master/profile-updates` lista `changed` com campo, texto no Mestre e no Perfil; `POST /master/profile-refresh` atualiza só os escolhidos, idempotente, com versão do Mestre | `test_an_edited_profile_fact_is_listed_with_before_and_after`, `test_refresh_updates_the_master_entry_only_and_is_idempotent`, `test_the_api_lists_changed_facts_and_refreshes_on_request`, E2E com API real |
| Direção da escrita | — | o Perfil nunca é escrito a partir do Mestre ou das variantes; variantes já criadas não mudam quando o Mestre muda | `test_refresh_updates_the_master_entry_only_and_is_idempotent` confere o Perfil depois |
| Rascunho do navegador restaurado | a mensagem dizia "será salvo em seguida", mas o editor o marcava como salvo e ele só ia ao servidor numa próxima edição | o rascunho restaurado fica pendente e o autosave o grava com a versão em que se baseou | `resume-editor-state.test.ts` |

Só entradas montadas a partir de um único fato são comparadas: uma entrada que a pessoa juntou de
vários fatos é dela. A diferença pode vir de uma edição no Perfil ou no Mestre; a tela diz isso e não
escolhe sozinha. No código anterior o módulo de teste nem importa (as funções e o erro de conflito não
existem).
