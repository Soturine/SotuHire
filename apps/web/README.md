# SotuHire Web

Frontend moderno do SotuHire em `apps/web` para a versao `v1.7.1`.

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
- Playwright para smoke/E2E/cross-browser

## Rodar localmente

Fluxo principal, a partir da raiz do repositorio:

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

Build e validacao:

```powershell
cd apps/web
npm run build
npm run lint
npm run typecheck
npm run test:e2e
npm run test:e2e:cross-browser
```

Para iniciar tambem a Local Companion API usada pela extensao assistiva:

```powershell
.\start-sotuhire.ps1 -WithCompanion
```

## Configuracao da API

Crie um `.env.local` local se quiser trocar a URL padrao:

```env
VITE_SOTUHIRE_API_URL=http://127.0.0.1:8787/api/v1
```

O padrao do app e `http://127.0.0.1:8787/api/v1`.

## Modos

- **Modo Demo:** usa dados ficticios locais para explorar todas as telas.
- **Modo API Real:** consulta a FastAPI local em `/api/v1` e espera o envelope `{ ok, data, warnings, request_id }`.

O frontend nao calcula score real, nao move regra de negocio para o cliente e nao salva segredos. A
URL e o modo selecionados ficam apenas no estado da sessao aberta do app.

## Telas

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

## IA e Providers

A secao **IA e Providers** em Configuracoes usa endpoints reais da API local:

```txt
GET /api/v1/settings/ai
GET /api/v1/settings/ai/status
POST /api/v1/settings/ai
POST /api/v1/settings/ai/test
DELETE /api/v1/settings/ai
```

A chave digitada e enviada somente para o backend local e limpa do estado do componente apos salvar.
Ela nao e persistida em `localStorage`, `sessionStorage` ou bundle publico. A API nunca retorna a
chave; retorna apenas provider, modelo, `configured`, `status`, toggles, warnings e `updated_at`.

Estados exibidos na UI:

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

## Kanban e responsividade

O Kanban de Candidaturas usa status reais do backend, drag-and-drop visual, rollback quando a API
falha e select de status como alternativa para teclado/mobile. O teste responsivo valida:

```txt
Mobile: 390x844
Tablet: 768x1024
Desktop: 1440x1000
```

## Fontes e Captura

A tela **Fontes e Captura** inclui o fluxo `AUTHENTICATED_BROWSER` existente no backend local:

- testa o CDP local em `http://127.0.0.1:9222`;
- abre um Chromium dedicado para login manual;
- exige confirmacao de uso autorizado antes de coletar;
- chama `/api/v1/sources/authenticated-browser/*` no modo API Real.

A v1.7.1 nao altera scraper autenticado, Chromium/CDP, crawler logado, login manual, auto-apply ou
regras protegidas.

O painel **Extensao Local** consulta `/api/v1/extension/status` e `/api/v1/extension/captures` para
mostrar capturas ja salvas pela Local Companion API. Ele mostra status do companion, ultima
sincronizacao, origem, URL, data, tipo de captura e acoes para Vaga, GitHub Analysis e
Candidaturas. A v1.7.1 tambem permite marcar capturas locais como revisadas, ignoradas ou
arquivadas sem tocar em browser autenticado.

### Caixa de Entrada e importadores

Fontes e Captura inclui a **Caixa de Entrada de Oportunidades** para revisar entradas antes de
analisar ou salvar:

- texto colado manualmente;
- link manual com leitura publica simples;
- CSV com campos `cargo,empresa,link,local,descricao,fonte,status,observacoes`;
- JSON com os mesmos campos ou aliases em ingles;
- capturas da extensao/local companion.

O painel oferece busca, filtros por status/origem, deduplicacao local e acoes para **Importar para
Vaga**, **Salvar em Candidaturas**, **Copiar link**, **Arquivar** e **Ignorar**.

Na v1.7.1, CSV/JSON tambem podem ser enviados por upload do navegador. O app mostra preview das
primeiras linhas/itens e so importa depois de confirmacao. A Caixa tambem exporta todos, filtrados
ou selecionados em CSV/JSON, e a comparacao de duplicatas permite **Mesclar**, **Manter separado**,
**Arquivar novo** ou **Marcar como nao duplicata** preservando historico.

O **Diretório de Fontes** organiza paginas de carreira abertas, feeds RSS publicos, APIs oficiais,
CSV/JSON recorrente, links manuais e fontes observadas. RSS recorrente e APIs oficiais continuam
roadmap/planejado.

O importador de URL nao faz crawler amplo. Se uma pagina bloquear acesso, exigir login ou nao
permitir leitura publica simples, a API retorna um aviso para abrir a pagina manualmente e colar o
texto da vaga.

## Testes e screenshots

```powershell
cd apps/web
npm run test:e2e
```

O Playwright cobre Home, Dashboard, fluxo guiado, demos de analise, IA Settings, Fontes e Captura,
Kanban, cross-browser em Chromium/Firefox/WebKit e ausencia de branding legado publico. O spec
`visual-capture.spec.ts` gera screenshots em:

```txt
docs/assets/screenshots/sotuhire-v1.7.1-web-*.png
```

Todos usam viewport `1440x1000`, `deviceScaleFactor=1` e `fullPage=false`.

## Seguranca e limites

- Sem auto apply.
- Sem automacao de LinkedIn, Gupy ou plataformas similares.
- Sem API keys em `localStorage`, `sessionStorage` ou bundle publico.
- GitHub Pages continua estatico/demo-oriented.
- Backend/core continuam responsaveis por regras, score e validacoes.
- Streamlit permanece disponivel como modo legado/dev/local debug.
