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

- Fatos editados no Perfil depois de projetados não atualizam a entrada já existente no Mestre (só
  fatos novos aparecem como atualização). Decidir entre "propor edição" e manter o texto do documento.
- `LocalStore` ainda é usado por Application Lab, Local API, Radar, fontes e Tracker; a retirada segue
  a política de migração com backup e rollback e não foi feita neste ciclo.
- Não verificado: dois navegadores editando a mesma variante ao mesmo tempo (não há controle de versão
  otimista na API de variantes).
