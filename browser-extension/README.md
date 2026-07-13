# SotuHire Assistive Browser Companion

Extensão Manifest V3 para transformar a página aberta em uma captura revisável do SotuHire. Ela
trabalha com vagas, editais/concursos, candidaturas já realizadas e sinais públicos de GitHub ou
portfólio, sem automatizar login ou candidatura.

A extensão pode funcionar sozinha para copiar conteúdo visível e analisar projetos públicos no
navegador. Quando a Local Companion API está ativa, ela também salva capturas, cria snapshots,
envia itens ao Tracker e disponibiliza candidatos para revisão no Perfil Profissional Universal.
O site continua funcionando sem a extensão, e a extensão não depende do frontend React estar
aberto.

![Popup principal](../docs/assets/screenshots/extension/popup-main.png)

## Modos de uso

| Modo | Precisa do SotuHire local? | Precisa de chave? | O que entrega |
| --- | --- | --- | --- |
| Local no navegador | Não | Não | Análise determinística de GitHub/portfólio, cópia e preparação de capturas. |
| Gemini próprio | Não, para analisar projetos | Chave Gemini da pessoa usuária | Catálogo de modelos e análise real pelo Gemini. |
| OpenAI própria | Não, para analisar projetos | Chave OpenAI da pessoa usuária | Catálogo de modelos e análise real pela OpenAI. |
| IA do SotuHire | Sim | Configurada somente no backend local | Análise conectada, contexto seguro e rastreabilidade do provider usado. |
| Companion sem IA externa | Sim | Não | Captura, snapshots, análise local, Tracker, fila e integração com o site. |

As chaves próprias Gemini/OpenAI refinam a análise de projetos públicos. Match e ATS de uma vaga
usam a Local Companion; quando **IA configurada no SotuHire** está selecionada, a chave permanece
exclusivamente no backend local.

## O que a extensão faz

### Vagas e candidaturas

- captura título, empresa, localização, descrição, URL e texto visível da aba atual;
- prioriza JSON-LD `schema.org/JobPosting` quando a página o fornece;
- usa seletores semânticos e texto visível como fallback;
- analisa a vaga com Match/ATS local ou com a IA configurada no SotuHire;
- envia a vaga ao Tracker preservando a origem e o anúncio usado;
- acumula páginas de candidaturas já realizadas em lote, com limite de 500 itens por envio;
- deduplica URLs equivalentes, inclusive parâmetros comuns de tracking.

A captura é assistida: a pessoa abre a página e clica na ação desejada. A extensão não percorre
listas por conta própria e não clica em botões nativos de candidatura.

### Editais e concursos

Uma página pública pode ser capturada como `public_exam`. O SotuHire salva o texto e a estrutura
disponível em um snapshot de edital e oferece importação como rascunho revisável. A captura não se
torna candidatura, inscrição ou evidência profissional automaticamente.

### GitHub e portfólio

Em páginas públicas, a extensão coleta somente sinais disponíveis sem autenticação adicional:

- README e descrição;
- arquivos centrais visíveis;
- mensagens de commit públicas;
- linguagens e topics;
- metadados públicos obtidos pela API do GitHub, sem token e com `credentials: omit`.

Em `github.com`, o botão **SotuHire Insight** abre um modal com score, stack, documentação,
arquitetura, manutenção, pontos fortes, gaps, recomendações e evidências seguras para currículo. O
modelo selecionado é usado na chamada real; ele não é apenas uma preferência visual.

O modo **Deep analysis** aumenta a amostra de arquivos e commits públicos. Ele não libera conteúdo
privado, não usa cookies e não contorna limites do GitHub.

### Perfil Profissional Universal

Capturas e projetos podem gerar `ProfileItem` candidatos com `source`, `source_ref`, confiança e
evidência curta. Esses itens chegam como `confirmed_by_user=false`. Nada entra no Perfil sem a
seleção e a confirmação explícitas da pessoa usuária.

Uma vaga pode sugerir objetivo, preferência ou gap; ela não comprova uma habilidade. Projetos
públicos podem sugerir projeto, skill, produção técnica ou evidência acadêmica, sempre sujeitos à
revisão humana.

## Instalação local

### Carregar a pasta no Chromium

1. Abra `chrome://extensions` ou a página equivalente do navegador Chromium.
2. Ative **Modo do desenvolvedor**.
3. Clique em **Carregar sem compactação**.
4. Selecione a pasta `browser-extension/`.
5. Fixe o SotuHire na barra do navegador, se desejar.

Para testar um ZIP gerado pelo projeto, extraia-o primeiro e carregue a pasta resultante. O arquivo
`manifest.json` informa a versão instalada; a implementação atual usa a linha `0.9.2`.

### Iniciar a integração local

No Windows:

```powershell
.\start-sotuhire.ps1 -WithCompanion
```

Em qualquer sistema com o ambiente Python preparado:

```bash
python -m modules.local_api.server
```

A Local Companion escuta somente em `127.0.0.1:8765`. A API do site usa `127.0.0.1:8787`; nenhuma
das duas deve ser publicada na rede para o uso normal.

No site, abra **Fontes e Captura > Extensão Local** para revisar capturas, importar vagas ou
editais, enviar itens ao Tracker e gerar candidatos para o Perfil.

## Configuração de IA

Abra a aba **IA** do popup e escolha um modo.

### IA configurada no SotuHire

A extensão envia os sinais públicos ao backend local. O backend escolhe provider e modelo conforme
a configuração do SotuHire e devolve apenas o relatório e metadados de execução. A chave do app
nunca é enviada ao popup, à página ou ao content script.

### Gemini ou OpenAI próprios

1. Escolha **Google Gemini — chave própria** ou **OpenAI — chave própria**.
2. Use o link **Obter chave oficial** para abrir a página do provider.
3. Cole uma chave válida no campo mascarado.
4. Mantenha desmarcada a opção de persistência para usar somente a sessão do navegador.
5. Clique em **Salvar e validar**.
6. Escolha um modelo retornado pelo catálogo e inicie a análise.

O service worker consulta o catálogo oficial ao validar a chave, quando o cache de seis horas
expira ou quando a pessoa clica em **Atualizar catálogo**. Em falha de rede, a extensão mostra um
warning e usa o último cache válido ou uma lista builtin. A seleção do modelo é persistida como
preferência; a chave não acompanha essa preferência.

### Análise local

O modo **Análise local — sem chave** produz um relatório determinístico. Também é o fallback
seguro quando um provider externo falha. O relatório informa `provider_requested`,
`provider_used`, modelo, modo de análise e motivo do fallback; a troca não deve ser silenciosa.

## Como as chaves são tratadas

- por padrão, a chave própria fica em `chrome.storage.session` e termina com a sessão do navegador;
- a opção **Manter a chave neste perfil do navegador** exige consentimento explícito;
- quando consentida, a persistência usa IndexedDB local acessível pelo service worker;
- IndexedDB é isolamento local, não uma alegação de criptografia adicional;
- a extensão nunca usa `chrome.storage.sync` para segredos;
- content scripts, página aberta, Local Companion e SotuHire não recebem a chave própria;
- logs, relatórios, fila offline, exportações e pacotes não devem conter a chave;
- **Remover chave** apaga a sessão, o registro persistente e resíduos de formatos antigos.

O campo **Token opcional do Local Companion** é diferente de uma chave de IA. Ele corresponde a
`SOTUHIRE_COMPANION_TOKEN`, protege chamadas localhost e também não deve aparecer em exportações.

Ao escolher Gemini ou OpenAI, os sinais públicos usados na análise são enviados ao provider
selecionado. Não analise repositórios privados ou conteúdo sensível como se fossem públicos.

## Handshake e compatibilidade

O popup envia sua versão ao endpoint `POST /handshake` da Local Companion. A resposta informa:

```json
{
  "extension_version": "0.9.2",
  "companion_version": "1.9.6",
  "api_version": "v1",
  "capabilities": [],
  "compatible": true,
  "warnings": []
}
```

O diagnóstico mostra versões, capacidades e warnings. Um Companion antigo continua sendo tratado
de forma compatível quando responde ao health check, mas o popup avisa que o handshake não está
disponível. Uma versão incompatível não é apresentada como conexão saudável.

O site também expõe `POST /api/v1/extension/handshake` para validar a ponte entre frontend,
FastAPI, Companion e extensão.

## Fila offline

Quando uma ação conectada falha, o payload permanece em `chrome.storage.local` como pendência. A
fila:

- deduplica por endpoint e URL normalizada;
- registra `retry_count`, `last_error`, `next_retry_at`, `state` e `max_attempts`;
- usa backoff exponencial a partir de 30 segundos;
- limita cada item a cinco tentativas automáticas/manuais;
- preserva itens falhos para revisão, nova captura ou exportação;
- recalcula identidades ao importar para impedir duplicação por parâmetros de tracking.

**Exportar fila** gera um JSON portátil sem campos cujo nome indique chave, token, cookie ou
credencial; valores com formato de chave Gemini/OpenAI também são redigidos. **Importar fila** aceita
somente o formato do SotuHire, até 500 itens e paths sob `/capture/`. A fila não usa
`chrome.storage.sync` e não faz parte do backup geral do app.

## Snapshots e histórico

A extensão prepara o payload; a Local Companion cria os snapshots imutáveis no banco local:

- `JobSnapshot` para vagas capturadas;
- `PublicExamSnapshot` para editais;
- `ResumeSnapshot` do contexto usado, quando disponível;
- `AnalysisSnapshot` para Match/ATS e rastreabilidade de provider/modelo/fallback.

O `snapshot_id` volta na resposta e acompanha a captura ou o Tracker. Repetir uma captura idêntica
reutiliza sua identidade de conteúdo; uma mudança real cria novo snapshot no histórico. O anúncio
continua disponível no Tracker mesmo se a página original sair do ar.

## Dados, backup e remoção

| Local | Conteúdo |
| --- | --- |
| `chrome.storage.local` | preferências, modelos escolhidos, lotes e fila offline; nunca a chave própria atual |
| `chrome.storage.session` | chave própria temporária, quando configurada sem persistência |
| IndexedDB do service worker | chave própria somente após consentimento explícito |
| `data/companion/` | capturas e contexto seguro da Local Companion |
| `data/sotuhire.db` | snapshots, aplicações e metadados persistidos pelo app local |

O backup do SotuHire exclui deliberadamente `chrome.storage`, IndexedDB, chaves, tokens e cookies.
Para transportar apenas pendências, use o exportador sanitizado da fila. Remover a extensão elimina
o estado do navegador, mas não apaga dados já importados no SotuHire; esses dados devem ser
gerenciados pelo app local.

## Permissões e limites

| Permissão/host | Motivo |
| --- | --- |
| `activeTab` | ler a aba atual somente após ação explícita |
| `scripting` | executar o extrator assistivo na aba selecionada |
| `storage` | guardar preferências, fila e segredo consentido nos storages descritos acima |
| `127.0.0.1:8765` | Local Companion |
| `127.0.0.1:8787` | API local do SotuHire |
| `github.com` e `api.github.com` | botão contextual e dados públicos de projetos |
| APIs Gemini/OpenAI | catálogo e análise somente quando o provider próprio é escolhido |

A extensão não solicita `<all_urls>`, cookies, histórico, downloads, `webRequest` ou acesso a
headers autenticados. Ela não:

- faz login ou guarda senha;
- captura cookies, tokens, sessão ou storage de terceiros;
- burla CAPTCHA, checkpoint ou rate limit;
- faz scraping em massa;
- aplica a vagas ou inscreve em concursos;
- paga taxas, emite boleto, envia documentos ou mensagens;
- transforma resultado de IA em decisão crítica sem revisão humana.

O fluxo `authenticated-browser` é separado da extensão assistiva e não compartilha credenciais,
cookies ou sessão com ela.

## Capturas de tela

| Estado | Imagem |
| --- | --- |
| Popup e conexão | [popup](../docs/assets/screenshots/extension/popup-main.png) · [conectada](../docs/assets/screenshots/extension/status-connected.png) |
| Vaga e edital | [vaga](../docs/assets/screenshots/extension/capture-job.png) · [edital](../docs/assets/screenshots/extension/capture-public-exam.png) |
| GitHub | [captura](../docs/assets/screenshots/extension/capture-github.png) · [análise](../docs/assets/screenshots/extension/github-analysis-modal.png) |
| IA e contexto | [provider](../docs/assets/screenshots/extension/ai-provider-setup.png) · [contexto seguro](../docs/assets/screenshots/extension/safe-context.png) |
| Offline | [Companion offline](../docs/assets/screenshots/extension/companion-offline.png) |

As imagens são produzidas por `scripts/capture_extension_screenshots.py` com dados fictícios,
sem chaves e sem informações pessoais.

## Empacotar e testar

Na raiz do repositório:

```bash
node --check browser-extension/queue_runtime.js
node --check browser-extension/popup.js
node --check browser-extension/background.js
node --check browser-extension/content.js
node --check browser-extension/project_analysis.js
node --check browser-extension/github_injected.js
pytest -q -k "extension or browser"
python scripts/package_extension.py
```

O empacotador valida Manifest V3, permissões, arquivos de runtime, ícones e padrões de segredo
Gemini/OpenAI/GitHub. O ZIP executável contém somente o necessário para a extensão; documentação,
testes e materiais da loja ficam fora.

## Solução de problemas

- **Companion offline:** inicie `python -m modules.local_api.server`; a pendência permanece na fila.
- **Companion antigo:** abra o diagnóstico e compare as versões mínima e máxima informadas.
- **Catálogo indisponível:** confirme a chave, a rede e o warning; o fallback não apaga o cache.
- **Botão GitHub ausente:** recarregue a página e confirme que a extensão tem acesso a `github.com`.
- **Item não aparece no Perfil:** gere candidatos no site e confirme explicitamente os selecionados.
- **Chave não deve persistir:** deixe a opção de persistência desmarcada ou use **Remover chave**.

## Documentação relacionada

- [Local Companion API](../docs/02-architecture/local-companion-api.md)
- [Ponte com o Perfil Universal](../docs/02-architecture/extension-profile-bridge.md)
- [Regras de captura assistida](../docs/03-business-rules/browser-assisted-capture-rules.md)
- [Segurança e privacidade](../docs/06-engineering/security-privacy.md)
- [Testes da extensão](../docs/09-testing/browser-extension-testing.md)
- [Publicação na Chrome Web Store](../docs/07-development/chrome-web-store-extension.md)
