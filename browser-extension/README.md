# SotuHire Assistive Browser Companion

Extensão Manifest V3 para capturar a página atual ou uma lista visível de candidaturas e enviar os
dados para a Local Companion API em `http://127.0.0.1:8765`.

## Instalação local

1. Abra a página de extensões do Chromium.
2. Ative o modo desenvolvedor.
3. Escolha **Carregar sem compactação**.
4. Selecione a pasta `browser-extension/`.
5. Inicie a Local Companion API pela aba **Extensão** no SotuHire.

Na v1.8.1 do frontend moderno, também é possível iniciar o projeto com:

```powershell
.\start-sotuhire.ps1 -WithCompanion
```

Depois abra **Fontes e Captura -> Extensão Local** para ver capturas já salvas, revisar historico,
arquivar itens locais e importar para Vaga, GitHub Analysis ou Candidaturas. A extensão continua
usando a Local Companion API em `127.0.0.1:8765`.

As capturas tambem aparecem na **Caixa de Entrada de Oportunidades** do frontend moderno, junto de
vagas importadas por texto, link, CSV e JSON. Na v1.8.1, a Caixa tambem permite upload CSV/JSON com
preview, mescla visual de duplicatas e exportacao local. O usuario revisa antes de salvar/analisar.

Na v1.8.1, a compatibilidade com a extensão/local companion foi mantida. A mudança principal fica no
Radar de Vagas e na criação de wishlist com IA/local; nenhum fluxo de browser autenticado,
Chromium/CDP, crawler logado, cookie, token, sessão, CAPTCHA ou auto-apply foi alterado.

## Portais compatíveis

A extensão usa permissões `activeTab` e heurísticas genéricas, então pode trabalhar com a página
atual de LinkedIn, Gupy, Indeed, InfoJobs, Nube, páginas de carreira e outros portais. O portal não
precisa estar previamente cadastrado no SotuHire.

## Importar candidaturas paginadas

1. Abra manualmente a lista de candidaturas no portal.
2. Em cada página, clique em **Adicionar página ao lote**.
3. Navegue para a próxima página e repita.
4. Clique em **Enviar lote acumulado**.

O lote fica temporariamente no storage local da extensão e aceita até 500 registros por envio. A
API e o tracker deduplicam por URL normalizada e por empresa+título semelhante. Se LinkedIn levar a
candidatura para Gupy ou outro portal, o SotuHire mantém um cartão e registra as duas fontes.

## GitHub, projetos e portfólios

Em uma página pública de perfil GitHub, repositório, projeto ou portfólio, a extensão extrai o
conteúdo visível, README, arquivos centrais, mensagens de commit, linguagens e topics.

Em `github.com`, a extensão injeta o botão **SotuHire AI** próximo às ações do repositório ou,
como fallback, ao cabeçalho visível. O botão funciona em repositórios, árvores, arquivos e perfis
públicos. O modal oferece análise, cópia, exportação e envio para memória, evidências, perfil e
comparação com vaga.

Ela oferece dois modos:

- **Analisar projeto no navegador**: relatório standalone local; se uma chave Gemini standalone for
  configurada, o Gemini aprimora o texto do relatório;
- **Salvar projeto no SotuHire**: envia o payload à API local, gera relatório completo, salva
  memória/evidências e disponibiliza o projeto na aba **GitHub / Portfólio / Projetos**.

Arquivos gerados, binários, imagens, locks grandes, `node_modules`, `dist`, `build`, `.venv` e
`__pycache__` não entram na amostragem inteligente.

## Token local opcional

Se `SOTUHIRE_COMPANION_TOKEN` estiver configurado no SotuHire, informe o mesmo valor no campo
**Token local opcional** do popup. Esse token protege apenas a API localhost; ele não é uma chave de
provider de IA.

## Privacidade

- usa somente `activeTab`, `scripting`, `storage`, localhost e o host restrito `github.com`;
- processa a página que a pessoa abriu manualmente;
- não automatiza login e não guarda senha;
- não burla CAPTCHA;
- nunca recebe ou armazena a API Key configurada no SotuHire;
- a chave Gemini standalone opcional fica somente em `chrome.storage.local`;
- não lê cookies, tokens, `localStorage`, `sessionStorage` ou headers autenticados.

## Gerar o ZIP da Chrome Web Store

Na raiz do projeto:

```bash
python scripts/package_extension.py
```

O script valida Manifest V3, permissões, ícones, arquivos obrigatórios e segredos antes de gerar
`dist/sotuhire-extension-v0.9.0.zip`. Documentos e assets da listagem ficam em `store/` e não
entram no ZIP executável.

## Publicar

1. Execute os testes e gere o ZIP.
2. Crie ou atualize a listagem na Chrome Web Store.
3. Use `store/description-short.txt`, `store/description-full.md` e `store/listing.md`.
4. Informe a política em `store/privacy-policy.md`.
5. Envie as screenshots controladas e siga `store/test-instructions.md`.
