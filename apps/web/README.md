# SotuHire Web

Frontend moderno do SotuHire em `apps/web` para a versão `v1.5.1`.

## Stack

- React 19
- Vite
- TypeScript
- TanStack Router
- TanStack Query
- Tailwind CSS 4
- Radix UI
- Recharts
- lucide-react
- Playwright para smoke/E2E

## Rodar localmente

Fluxo principal, a partir da raiz do repositório:

```powershell
.\start-sotuhire.ps1
```

O launcher sobe:

- API: `http://127.0.0.1:8787`
- API docs: `http://127.0.0.1:8787/docs`
- Frontend: `http://localhost:5173`
- Local Companion opcional: `http://127.0.0.1:8765`

Manual:

```powershell
python scripts/run_api.py
cd apps/web
npm install
npm run dev
```

Build e validação:

```powershell
cd apps/web
npm run build
npm run lint
npm run typecheck
npm run test:e2e
```

Para iniciar também a Local Companion API usada pela extensão assistiva:

```powershell
.\start-sotuhire.ps1 -WithCompanion
```

## Configuração da API

Crie um `.env.local` local se quiser trocar a URL padrão:

```env
VITE_SOTUHIRE_API_URL=http://127.0.0.1:8787/api/v1
```

O padrão do app é `http://127.0.0.1:8787/api/v1`.

## Modos

- **Modo Demo:** usa dados fictícios locais para explorar todas as telas.
- **Modo API Real:** consulta a FastAPI local em `/api/v1` e espera o envelope `{ ok, data, warnings, request_id }`.

O frontend não calcula score real, não move regra de negócio para o cliente e não salva segredos. A
URL e o modo selecionados ficam apenas no estado da sessão aberta do app.

## Telas

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

## IA e Providers

A seção **IA e Providers** em Configurações usa endpoints reais da API local:

```txt
GET /api/v1/settings/ai
GET /api/v1/settings/ai/status
POST /api/v1/settings/ai
POST /api/v1/settings/ai/test
DELETE /api/v1/settings/ai
```

A chave digitada é enviada somente para o backend local e limpa do estado do componente após salvar.
Ela não é persistida em `localStorage`, `sessionStorage` ou bundle público. A API nunca retorna a
chave; retorna apenas provider, modelo, `configured`, `status`, toggles, warnings e `updated_at`.

Armazenamento local backend-side:

```txt
data/settings/ai-settings.json
data/secrets/ai-provider.local.json
```

`data/` e os arquivos locais de segredo são ignorados pelo Git.

Providers:

- `local`: sem chamada externa.
- `gemini`: usa a integração backend existente quando há chave local e o toggle da área está ativo.
- `openai_future`: aparece como planejado.

As telas de Currículo, Vaga, Compatibilidade, ATS, Tailor e GitHub mostram badges de **Análise
local**, **Análise com IA** e **Fallback local**. Se o Gemini falhar, a API retorna fallback local
com warning.

## Fontes e Captura

A tela **Fontes e Captura** inclui o fluxo `AUTHENTICATED_BROWSER` existente no backend local:

- testa o CDP local em `http://127.0.0.1:9222`;
- abre um Chromium dedicado para login manual;
- exige confirmação de uso autorizado antes de coletar;
- chama `/api/v1/sources/authenticated-browser/*` no modo API Real.

A v1.5.1 não altera o scraper autenticado, Chromium/CDP, crawler logado, login manual, auto-apply ou
regras protegidas. O fluxo não automatiza login, não contorna CAPTCHA/checkpoint e não envia
candidatura.

A v1.5.1 melhora o painel **Extensão Local**, que consulta `/api/v1/extension/status` e
`/api/v1/extension/captures` para mostrar capturas já salvas pela Local Companion API. O painel
mostra status do companion, origem, data, tipo de captura e pode importar uma captura para Vaga,
GitHub Analysis ou Candidaturas sem controlar contas de terceiros.

## Testes e screenshots

```powershell
cd apps/web
npm run test:e2e
```

O Playwright cobre Home, Dashboard, fluxo guiado, demos de análise, IA Settings, Fontes e Captura,
Kanban e ausência de branding legado público. O spec `visual-capture.spec.ts` gera screenshots em:

```txt
docs/assets/screenshots/sotuhire-v1.5.1-web-*.png
```

Todos usam viewport `1440x1000`, `deviceScaleFactor=1` e `fullPage=false`.

## Segurança e limites

- Sem auto apply.
- Sem automação de LinkedIn, Gupy ou plataformas similares.
- Sem API keys em `localStorage`, `sessionStorage` ou bundle público.
- GitHub Pages continua estático/demo-oriented.
- Backend/core continuam responsáveis por regras, score e validações.
- Streamlit permanece disponível como modo legado/dev/local debug.
