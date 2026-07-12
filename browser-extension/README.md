# SotuHire Assistive Browser Companion

Extensão Manifest V3 para capturar a página atual, uma lista visível de candidaturas, um edital/concurso ou um projeto público e enviar os dados para a Local Companion API em `http://127.0.0.1:8765`.

O app SotuHire v1.9.5 é compatível com a extensão v0.9.1. A extensão tem versionamento independente.

## Instalação Local

1. Abra a página de extensões do Chromium.
2. Ative o modo desenvolvedor.
3. Escolha **Carregar sem compactação**.
4. Selecione a pasta `browser-extension/`.
5. Inicie a Local Companion API pela aba **Extensão** no SotuHire.

Também é possível iniciar o projeto com:

```powershell
.\start-sotuhire.ps1 -WithCompanion
```

Depois abra **Fontes e Captura > Extensão Local** para ver capturas salvas, revisar histórico, arquivar itens locais, importar para Vaga/Editais/GitHub/Candidaturas e gerar evidências candidatas para o Perfil Profissional Universal.

## Ponte com o Perfil Universal

Capturas e projetos podem virar `ProfileItem` candidatos revisáveis. O site chama:

```txt
GET  /api/v1/extension/context
POST /api/v1/extension/import/public-exam
POST /api/v1/extension/captures/{capture_id}/profile-candidates
POST /api/v1/extension/captures/{capture_id}/add-to-profile
POST /api/v1/extension/projects/{project_id}/profile-candidates
POST /api/v1/extension/projects/{project_id}/add-to-profile
```

Esses candidatos usam `source` como `extension_capture`, `github_capture`, `portfolio_capture` ou `browser_assisted_capture`, preservam `source_ref` com `capture_id` ou `project_id`, carregam evidência textual curta e ficam com `confirmed_by_user=false` até a pessoa confirmar no site.

Capturas de edital/concurso usam `kind=public_exam`, são importadas como rascunho revisável em **Editais / Concursos** e não viram candidatura privada nem evidência profissional automaticamente.

Uma vaga capturada pode gerar objetivo, preferência ou gap a revisar. Ela não vira habilidade profissional automaticamente. Projetos GitHub/portfólio podem gerar projeto, skill, produção técnica ou evidência acadêmica candidata, sempre com revisão humana.

## Portais Compatíveis

A extensão usa permissões `activeTab` e heurísticas genéricas, então pode trabalhar com a página atual de LinkedIn, Gupy, Indeed, InfoJobs, Nube, páginas de carreira e outros portais. O portal não precisa estar previamente cadastrado no SotuHire.

## Importar Candidaturas Paginadas

1. Abra manualmente a lista de candidaturas no portal.
2. Em cada página, clique em **Adicionar página ao lote**.
3. Navegue para a próxima página e repita.
4. Clique em **Enviar lote acumulado**.

O lote fica temporariamente no storage local da extensão e aceita até 500 registros por envio. A API e o tracker deduplicam por URL normalizada e por empresa + título semelhante.

Se a Local Companion estiver offline, capturas e ações de envio ficam em uma fila temporária. O botão **Reenviar pendências offline** tenta sincronizar novamente; copiar texto e analisar projetos localmente continuam disponíveis sem o frontend React aberto.

## GitHub, Projetos e Portfólios

Em uma página pública de perfil GitHub, repositório, projeto ou portfólio, a extensão extrai conteúdo visível, README, arquivos centrais, mensagens de commit, linguagens e topics.

Em `github.com`, a extensão injeta o botão **SotuHire Insight** perto das ações do repositório ou, como fallback, no cabeçalho visível. O modal oferece análise, provider/modelo funcional, cópia, exportação e envio para memória, evidências, Perfil e comparação com vaga.

Modos principais:

- **Analisar projeto no navegador**: funciona localmente, com a IA configurada no SotuHire ou com Gemini/OpenAI próprios da extensão.
- **Salvar projeto no SotuHire**: envia o payload à API local, gera relatório completo, salva memória/evidências e disponibiliza o projeto no SotuHire.
- **Gerar evidência para Perfil**: envia o projeto ao SotuHire local para que o site gere candidatos revisáveis. Nada entra no Perfil sem confirmação do usuário.

Arquivos gerados, binários, imagens, locks grandes, `node_modules`, `dist`, `build`, `.venv` e `__pycache__` não entram na amostragem inteligente.

## IA, Catálogo de Modelos e Token Local

Se `SOTUHIRE_COMPANION_TOKEN` estiver configurado no SotuHire, informe o mesmo valor no campo **Token local opcional** do popup. Esse token protege apenas a API localhost; ele não é uma chave de provider de IA.

Modos disponíveis para GitHub/portfólio:

- **IA configurada no SotuHire**: a chave continua exclusivamente no backend local;
- **Gemini da extensão**: link oficial para obter a chave e catálogo consultado em `generativelanguage.googleapis.com`;
- **OpenAI da extensão**: link oficial para obter a chave e catálogo consultado em `api.openai.com`;
- **Local sem chave**: análise determinística e fallback sempre disponível.

O modelo escolhido no popup ou no modal do GitHub é enviado na chamada real. O catálogo oficial é atualizado ao configurar a chave, periodicamente a cada seis horas e pelo botão **Atualizar catálogo**. Se a consulta falhar, o último cache ou a lista builtin segura permanece disponível com warning explícito.

Segredos próprios são controlados pelo service worker `background.js`, não pelos content scripts. Por padrão a chave fica em `chrome.storage.session` e desaparece ao fechar o navegador. Ao marcar **Manter a chave neste perfil do navegador**, ela vai para um cofre IndexedDB privado do service worker. A extensão nunca usa `chrome.storage.sync`, nunca injeta a chave na página e nunca a envia ao SotuHire.

Para aprofundar perfis e repositórios, o service worker consulta somente a API pública do GitHub, com `credentials: omit`, sem token e sem sessão. A coleta limitada cobre metadados públicos, repositórios, README, commits, linguagens, topics e árvore de arquivos. Rate limit ou falha de rede preservam a captura visível e o fallback local.

Na v1.9.5, a extensão envia texto visível para a Local Companion/API local e consulta apenas `context-summary` seguro, sem receber Perfil completo, memória completa ou API key.

## Privacidade

- usa `activeTab`, `scripting`, `storage` e hosts restritos a localhost, GitHub público, Gemini e OpenAI;
- processa a página que a pessoa abriu manualmente;
- não automatiza login;
- não automatiza candidatura;
- não burla CAPTCHA;
- não coleta cookies, tokens, sessão, headers, `localStorage` ou `sessionStorage`;
- não acessa a API key configurada no app; chaves próprias opcionais permanecem isoladas no service worker;
- exige revisão humana antes de salvar evidências no Perfil.

O fluxo `/api/v1/sources/authenticated-browser/*`, Chromium/CDP e `/authenticated-browser/collect` permanece separado e não é alterado pela extensão.

## Gerar o ZIP da Chrome Web Store

Na raiz do projeto:

```bash
python scripts/package_extension.py
```

O script valida Manifest V3, permissões, ícones, arquivos obrigatórios e segredos antes de gerar `dist/sotuhire-extension-v0.9.1.zip`. Documentos e assets da listagem ficam em `store/` e não entram no ZIP executável.

## Publicar

1. Execute os testes e gere o ZIP.
2. Crie ou atualize a listagem na Chrome Web Store.
3. Use `store/description-short.txt`, `store/description-full.md` e `store/listing.md`.
4. Informe a política em `store/privacy-policy.md`.
5. Envie as screenshots controladas e siga `store/test-instructions.md`.
