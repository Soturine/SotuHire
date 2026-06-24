# Frontend moderno

A v1.6.0 consolida o frontend moderno do SotuHire em `apps/web` como experiencia local principal,
com QA cross-browser, responsividade validada, Kanban com drag-and-drop e estados de IA/fallback
mais claros.

O app usa React, Vite, TypeScript, TanStack Router, TanStack Query, Tailwind CSS, Radix UI, Recharts
e lucide-react. Ele roda separado do Streamlit e consome a FastAPI local em `/api/v1` quando o modo
API Real esta ativo.

## Como rodar

Fluxo principal:

```powershell
.\start-sotuhire.ps1
```

Manual:

```powershell
python scripts/run_api.py
cd apps/web
npm install
npm run dev
```

Valide o frontend:

```powershell
cd apps/web
npm run build
npm run lint
npm run typecheck
npm run test:e2e
```

Para iniciar tambem a Local Companion API:

```powershell
.\start-sotuhire.ps1 -WithCompanion
```

## Modos

- **Modo Demo:** usa mocks ficticios locais e permite navegar sem backend ativo.
- **Modo API Real:** usa `http://127.0.0.1:8787/api/v1`.

## Telas integradas

- Home/Landing
- Dashboard
- Curriculo
- Vaga
- Analise de Compatibilidade
- Analise ATS
- Ajuste de Curriculo
- Analise de GitHub
- Candidaturas
- Inteligencia de Candidaturas
- Fontes e Captura
- Configuracoes
- Privacidade

## Cross-browser e responsividade

`npm run test:e2e` roda Playwright em:

```txt
chromium
firefox
webkit
```

A matriz responsiva e capturada uma vez no Chromium:

```txt
Mobile: 390x844
Tablet: 768x1024
Desktop: 1440x1000
```

## Kanban

O Kanban de Candidaturas usa status reais do backend, drag-and-drop visual, rollback se a API falhar
e select de status como alternativa acessivel para teclado/mobile.

## Fontes e Captura

A tela **Fontes e Captura** fica na rota `/sources` e no menu lateral. Ela organiza caminhos seguros
para colar vaga manualmente, salvar link, importar arquivo, usar extensao assistida, radar publico e
APIs oficiais quando disponiveis.

O fluxo `AUTHENTICATED_BROWSER` existente no backend local tambem aparece nessa tela. A v1.6.0 nao
alterou scraper autenticado, Chromium/CDP, crawler logado ou docs protegidos. O fluxo nao contorna
CAPTCHA/checkpoint, nao automatiza candidatura e nao faz auto-apply.

O painel **Extensao Local** consulta capturas ja salvas pela Local Companion API, mostra status,
ultima sincronizacao, origem, URL, data e tipo de captura, e permite importar uma captura para Vaga,
GitHub Analysis ou Candidaturas. O botao Ignorar oculta a captura apenas na sessao da UI.

## IA e Providers

A secao **IA e Providers** em Configuracoes usa endpoints reais do backend local:

```txt
GET /api/v1/settings/ai
GET /api/v1/settings/ai/status
POST /api/v1/settings/ai
POST /api/v1/settings/ai/test
DELETE /api/v1/settings/ai
```

A chave e enviada apenas para a FastAPI local e armazenada backend-side em
`data/secrets/ai-provider.local.json`, com metadados seguros em `data/settings/ai-settings.json`.
Esses caminhos sao ignorados pelo Git. A chave nunca e retornada ao frontend, nao aparece em mocks,
prints ou docs e nao e gravada em `localStorage`/`sessionStorage`.

Estados exibidos:

```txt
IA desativada
Provider local
Provider configurado
Provider nao configurado
Analisando com IA
Fallback local
Limite/erro do provider
Timeout do provider
Chave invalida
```

## Testes e visual

```powershell
cd apps/web
npm run test:e2e
```

O Playwright cobre fluxo guiado, demos de analise, IA Settings, Fontes e Captura, Kanban,
cross-browser e ausencia de branding legado. O spec visual gera a serie `sotuhire-v1.6-web-*.png`
em `docs/assets/screenshots/` com viewport fixo `1440x1000`.

## Streamlit legado/dev

O Streamlit continua disponivel, mas nao e o fluxo principal do frontend moderno:

```powershell
streamlit run app.py
```

## Fronteira de responsabilidade

O frontend exibe estados, coleta inputs e chama a API. O backend/core continua responsavel por:

- extracao de curriculo e vaga;
- Analise de Compatibilidade;
- ATS;
- Resume Tailor;
- GitHub Analyzer;
- tracker, metricas e persistencia;
- configuracoes locais de IA e segredos;
- validacoes fortes;
- regras anti-invencao;
- privacidade e retencao local.

## GitHub Pages

O GitHub Pages continua estatico e demo-oriented. Ele nao roda Python, FastAPI, Streamlit, IA ou
storage local.

## Referencias

- [Arquitetura frontend](frontend-architecture.md)
- [API contract](api-contract.md)
- [Mock data contract](mock-data-contract.md)
- [Screen map](screen-map.md)
- [Frontend rules](frontend-rules.md)
- [Application Intelligence](application-intelligence.md)
