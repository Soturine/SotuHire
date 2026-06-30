# SotuHire Assistive Browser Companion

Extensao Manifest V3 para capturar a pagina atual, uma lista visivel de candidaturas ou um projeto
publico e enviar os dados para a Local Companion API em `http://127.0.0.1:8765`.

O app SotuHire v1.9.1 e compativel com a extensao v0.9.0. A extensao tem versionamento independente.

## Instalacao local

1. Abra a pagina de extensoes do Chromium.
2. Ative o modo desenvolvedor.
3. Escolha **Carregar sem compactacao**.
4. Selecione a pasta `browser-extension/`.
5. Inicie a Local Companion API pela aba **Extensao** no SotuHire.

Tambem e possivel iniciar o projeto com:

```powershell
.\start-sotuhire.ps1 -WithCompanion
```

Depois abra **Fontes e Captura -> Extensao Local** para ver capturas salvas, revisar historico,
arquivar itens locais, importar para Vaga/GitHub/Candidaturas e gerar evidencias candidatas para o
Perfil Profissional Universal.

## Ponte com o Perfil Universal

Na v1.9.1, capturas e projetos podem virar `ProfileItem` candidatos revisaveis. O site chama:

```txt
GET  /api/v1/extension/context
POST /api/v1/extension/captures/{capture_id}/profile-candidates
POST /api/v1/extension/captures/{capture_id}/add-to-profile
POST /api/v1/extension/projects/{project_id}/profile-candidates
POST /api/v1/extension/projects/{project_id}/add-to-profile
```

Esses candidatos usam `source` como `extension_capture`, `github_capture`, `portfolio_capture` ou
`browser_assisted_capture`, preservam `source_ref` com `capture_id` ou `project_id`, carregam
evidencia textual curta e ficam com `confirmed_by_user=false` ate a pessoa confirmar no site.

Uma vaga capturada pode gerar objetivo, preferencia ou gap a revisar. Ela nao vira habilidade
profissional automaticamente. Projetos GitHub/portfolio podem gerar projeto e skills candidatas,
tambem com revisao humana.

## Portais compativeis

A extensao usa permissoes `activeTab` e heuristicas genericas, entao pode trabalhar com a pagina
atual de LinkedIn, Gupy, Indeed, InfoJobs, Nube, paginas de carreira e outros portais. O portal nao
precisa estar previamente cadastrado no SotuHire.

## Importar candidaturas paginadas

1. Abra manualmente a lista de candidaturas no portal.
2. Em cada pagina, clique em **Adicionar pagina ao lote**.
3. Navegue para a proxima pagina e repita.
4. Clique em **Enviar lote acumulado**.

O lote fica temporariamente no storage local da extensao e aceita ate 500 registros por envio. A API
e o tracker deduplicam por URL normalizada e por empresa + titulo semelhante.

## GitHub, projetos e portfolios

Em uma pagina publica de perfil GitHub, repositorio, projeto ou portfolio, a extensao extrai conteudo
visivel, README, arquivos centrais, mensagens de commit, linguagens e topics.

Em `github.com`, a extensao injeta o botao **SotuHire AI** perto das acoes do repositorio ou, como
fallback, no cabecalho visivel. O modal oferece analise, copia, exportacao e envio para memoria,
evidencias, perfil e comparacao com vaga.

Modos principais:

- **Analisar projeto no navegador**: relatorio standalone local; se uma chave Gemini standalone for
  configurada, o Gemini aprimora o texto do relatorio.
- **Salvar projeto no SotuHire**: envia o payload a API local, gera relatorio completo, salva
  memoria/evidencias e disponibiliza o projeto no SotuHire.
- **Gerar evidencia para Perfil**: envia o projeto ao SotuHire local para que o site gere candidatos
  revisaveis. Nada entra no Perfil sem confirmacao do usuario.

Arquivos gerados, binarios, imagens, locks grandes, `node_modules`, `dist`, `build`, `.venv` e
`__pycache__` nao entram na amostragem inteligente.

## IA e token local

Se `SOTUHIRE_COMPANION_TOKEN` estiver configurado no SotuHire, informe o mesmo valor no campo
**Token local opcional** do popup. Esse token protege apenas a API localhost; ele nao e uma chave de
provider de IA.

A chave Gemini standalone opcional pode permanecer no popup, mas ela e separada da IA configurada no
app. A API key do app SotuHire nao e lida, exposta ou armazenada pela extensao.

## Privacidade

- usa somente `activeTab`, `scripting`, `storage`, localhost e o host restrito `github.com`;
- processa a pagina que a pessoa abriu manualmente;
- nao automatiza login;
- nao automatiza candidatura;
- nao burla CAPTCHA;
- nao coleta cookies, tokens, sessao, headers, `localStorage` ou `sessionStorage`;
- nao acessa a API key configurada no app;
- exige revisao humana antes de salvar evidencias no Perfil.

O fluxo `/api/v1/sources/authenticated-browser/*`, Chromium/CDP e `/authenticated-browser/collect`
permanece separado e nao e alterado pela extensao.

## Gerar o ZIP da Chrome Web Store

Na raiz do projeto:

```bash
python scripts/package_extension.py
```

O script valida Manifest V3, permissoes, icones, arquivos obrigatorios e segredos antes de gerar
`dist/sotuhire-extension-v0.9.0.zip`. Documentos e assets da listagem ficam em `store/` e nao entram
no ZIP executavel.

## Publicar

1. Execute os testes e gere o ZIP.
2. Crie ou atualize a listagem na Chrome Web Store.
3. Use `store/description-short.txt`, `store/description-full.md` e `store/listing.md`.
4. Informe a politica em `store/privacy-policy.md`.
5. Envie as screenshots controladas e siga `store/test-instructions.md`.
