# Frontend moderno

A v1.5.1 consolida o frontend moderno do SotuHire em `apps/web` como experiência local principal e
adiciona polimento de produto, fluxo guiado, estados Local/IA/Fallback e E2E expandido.
O app usa React, Vite, TypeScript, TanStack Router, TanStack Query, Tailwind CSS, Radix UI, Recharts
e lucide-react. Ele roda separado do Streamlit e consome a FastAPI local em `/api/v1` quando o modo
API Real está ativo.

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

Para iniciar também a Local Companion API:

```powershell
.\start-sotuhire.ps1 -WithCompanion
```

## Modos

- **Modo Demo:** usa mocks fictícios locais e permite navegar sem backend ativo.
- **Modo API Real:** usa `http://127.0.0.1:8787/api/v1`.

Configuração local opcional:

```env
VITE_SOTUHIRE_API_URL=http://127.0.0.1:8787/api/v1
```

## Telas integradas

- Home/Landing
- Dashboard
- Currículo
- Vaga
- Análise de Compatibilidade
- Análise ATS
- Ajuste de Currículo
- Análise de GitHub
- Candidaturas
- Inteligência de Candidaturas
- Fontes e Captura
- Configurações
- Privacidade

## Fontes e Captura

A tela **Fontes e Captura** fica na rota `/sources` e no menu lateral. Ela organiza caminhos seguros
para colar vaga manualmente, salvar link, importar arquivo, usar extensão assistida, radar público e
APIs oficiais quando disponíveis.

O fluxo `AUTHENTICATED_BROWSER` existente no backend local também aparece nessa tela. Ele testa o CDP
local, abre um Chromium dedicado para login manual e exige confirmação de uso autorizado antes da
coleta. A v1.5.1 não alterou o scraper autenticado, Chromium/CDP, crawler logado ou docs protegidos.
O fluxo não contorna CAPTCHA/checkpoint, não automatiza candidatura e não faz auto-apply.

O painel **Extensão Local** consulta capturas já salvas pela Local Companion API, mostra status,
origem, data e tipo de captura, e permite importar uma captura para Vaga, GitHub Analysis ou
Candidaturas. Ele não controla sites de terceiros.

## IA e Providers

A seção **IA e Providers** em Configurações usa endpoints reais do backend local:

```txt
GET /api/v1/settings/ai
GET /api/v1/settings/ai/status
POST /api/v1/settings/ai
POST /api/v1/settings/ai/test
DELETE /api/v1/settings/ai
```

A chave é enviada apenas para a FastAPI local e armazenada backend-side em
`data/secrets/ai-provider.local.json`, com metadados seguros em `data/settings/ai-settings.json`.
Esses caminhos são ignorados pelo Git. A chave nunca é retornada ao frontend, não aparece em mocks,
prints ou docs e não é gravada em `localStorage`/`sessionStorage`.

Providers:

- `local`: sem chamada externa.
- `gemini`: usa a integração backend existente quando há chave.
- `openai_future`: planejado para versão futura.

Na v1.5.1, os toggles em Configurações controlam o roteamento de IA no backend. As telas mostram
badges de **Análise local**, **Análise com IA** e **Fallback local**, mas a regra de negócio e os
scores finais seguem no Python.

## Testes e visual

```powershell
cd apps/web
npm run test:e2e
```

O Playwright cobre fluxo guiado, demos de análise, IA Settings, Fontes e Captura, Kanban e ausência
de branding legado. O spec visual gera a série `sotuhire-v1.5.1-web-*.png` em
`docs/assets/screenshots/` com viewport fixo `1440x1000`.

## Streamlit legado/dev

O Streamlit continua disponível, mas não é o fluxo principal do frontend moderno:

```powershell
streamlit run app.py
```

Use esse modo para debug local, validações antigas e fluxos de desenvolvimento que ainda dependem da
interface Streamlit.

## Fronteira de responsabilidade

O frontend exibe estados, coleta inputs e chama a API. O backend/core continua responsável por:

- extração de currículo e vaga;
- Análise de Compatibilidade;
- ATS;
- Resume Tailor;
- GitHub Analyzer;
- tracker, métricas e persistência;
- configurações locais de IA e segredos;
- validações fortes;
- regras anti-invenção;
- privacidade e retenção local.

## GitHub Pages

O GitHub Pages continua estático e demo-oriented. Ele não roda Python, FastAPI, Streamlit, IA ou
storage local.

## Referências

- [Arquitetura frontend](frontend-architecture.md)
- [API contract](api-contract.md)
- [Mock data contract](mock-data-contract.md)
- [Screen map](screen-map.md)
- [Frontend rules](frontend-rules.md)
- [Application Intelligence](application-intelligence.md)
