# Extension Profile Bridge

A Extension Profile Bridge conecta a extensão assistiva, Local Companion API, Career Context Engine
e Perfil Profissional Universal. Uma captura pode sugerir evidências, mas nada entra no Perfil sem
revisão e confirmação explícitas.

## Fluxo

```text
Pessoa abre vaga, edital, GitHub ou portfólio
  -> extensão extrai JSON-LD/sinais públicos/texto visível
  -> Local Companion valida, deduplica e cria snapshot
  -> FastAPI lista a captura no site
  -> Career Context seleciona somente evidências necessárias
  -> site mostra ProfileItems candidatos
  -> pessoa confirma os itens desejados
  -> Perfil Universal persiste itens confirmados com proveniência
```

## Endpoints do site

```txt
POST  /api/v1/extension/handshake
GET   /api/v1/extension/status
GET   /api/v1/extension/captures
GET   /api/v1/extension/context
PATCH /api/v1/extension/captures/{capture_id}
POST  /api/v1/extension/import/job
POST  /api/v1/extension/import/github
POST  /api/v1/extension/import/public-exam
POST  /api/v1/extension/import/tracker
POST  /api/v1/extension/captures/{capture_id}/profile-candidates
POST  /api/v1/extension/captures/{capture_id}/add-to-profile
POST  /api/v1/extension/projects/{project_id}/profile-candidates
POST  /api/v1/extension/projects/{project_id}/add-to-profile
```

`profile-candidates` gera rascunhos locais com `confirmed_by_user=false`, `source`, `source_ref`,
`confidence` e evidência curta. `add-to-profile` recebe apenas os candidatos selecionados e os salva
como confirmados pela pessoa usuária.

O handshake não transporta conteúdo de carreira. Ele informa versões, capabilities,
compatibilidade e warnings para impedir que frontend, Companion e extensão pareçam integrados
quando seus contratos divergem.

## Capturas, snapshots e proveniência

Capturas conectadas preservam:

- `capture_id` e URL de origem;
- `collection_method=browser_assisted_capture`;
- `extraction_strategy`, inclusive `schema_org_jobposting` quando disponível;
- `content_hash`, `snapshot_id` e histórico de snapshots;
- `source` e `source_ref` até Perfil, análise ou Tracker.

Vagas geram `JobSnapshot`; editais geram `PublicExamSnapshot`; análises podem ligar
`ResumeSnapshot` e `AnalysisSnapshot`. Alterar o status ou importar a captura não modifica o
snapshot original.

## Fontes e revisão

As fontes aceitas para candidatos incluem:

- `extension_capture`;
- `github_capture`;
- `portfolio_capture`;
- `browser_assisted_capture`.

Uma vaga não prova uma habilidade profissional. Ela pode sugerir objetivo, preferência, keyword ou
gap. Projetos GitHub/portfólio podem sugerir projeto, skill, produção técnica ou evidência
acadêmica, sempre com revisão humana.

Capturas `public_exam` não viram vaga privada, candidatura ou inscrição. Elas entram em
Editais/Concursos como rascunho revisável.

## Career Context

A extensão recebe somente um resumo para o propósito `extension`, com evidências confirmadas,
warnings e referências de origem. Perfil completo, memória completa e dados sensíveis não são
copiados para o popup.

Evidências acadêmicas ou Lattes já confirmadas podem participar do contexto seguro. Candidatos
acadêmicos vindos da extensão só entram em outros fluxos depois da confirmação.

## Privacidade

- a extensão não recebe a chave configurada no app;
- uma chave própria fica isolada no service worker e nunca entra na ponte;
- content scripts não recebem segredo, token local ou Perfil completo;
- fila e exportação removem campos nomeados como credencial e redigem valores com formato de chave;
- nenhum cookie, token, sessão, header autenticado ou storage de terceiros é coletado;
- nenhuma candidatura, inscrição ou mensagem é automatizada;
- authenticated-browser permanece um fluxo separado.

## Arquivos principais

```txt
apps/api/routes/extension.py
apps/api/services/extension.py
apps/api/schemas/extension.py
apps/web/src/routes/sources.tsx
modules/context
modules/local_api
modules/profile
modules/storage/snapshots.py
browser-extension/
tests/test_api_extension_bridge.py
tests/test_extension_reliability_runtime.py
```
