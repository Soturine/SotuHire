# Frontend moderno

A v1.7.1 consolida o frontend moderno do SotuHire em `apps/web` como experiencia local principal e
poliu a Caixa de Entrada de Oportunidades com upload CSV/JSON, preview, merge visual de duplicatas,
exportacao e Diretório de Fontes.

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

O fluxo `AUTHENTICATED_BROWSER` existente no backend local tambem aparece nessa tela. A v1.7.1 nao
alterou scraper autenticado, Chromium/CDP, crawler logado ou docs protegidos. O fluxo nao contorna
CAPTCHA/checkpoint, nao automatiza candidatura e nao faz auto-apply.

O painel **Extensao Local** consulta capturas ja salvas pela Local Companion API, mostra status,
ultima sincronizacao, origem, URL, data e tipo de captura, e permite importar uma captura para Vaga,
GitHub Analysis ou Candidaturas. A v1.7.1 tambem permite revisar, arquivar ou ignorar capturas no
historico local.

### Caixa de Entrada

A area **Caixa de Entrada de Oportunidades** em `/sources` mostra vagas importadas por texto, link,
CSV, JSON e capturas da extensao/local companion. Ela oferece filtros por status/origem, busca por
cargo/empresa/link/tag/origem, deduplicacao local e acoes para:

- importar para a tela Vaga;
- salvar em Candidaturas/Kanban;
- fazer upload CSV/JSON com preview antes de confirmar;
- mesclar duplicata preservando historico;
- exportar todos, filtrados ou selecionados em CSV/JSON;
- arquivar ou ignorar;
- copiar o link original.

O **Diretório de Fontes** mostra paginas de carreira abertas, feeds RSS publicos, APIs oficiais,
CSV/JSON recorrente, links manuais e fontes observadas. Feeds recorrentes e APIs oficiais continuam
roadmap/planejado.

CSV esperado:

```csv
cargo,empresa,link,local,descricao,fonte,status,observacoes
Analista de Dados,Empresa Exemplo,https://example.com/jobs/123,Remoto,"Python, SQL e dashboards",CSV Manual,nova,"vaga ficticia"
Desenvolvedor Backend,Tech Exemplo,https://example.com/jobs/456,Hibrido,"APIs, testes e bancos de dados",CSV Manual,nova,"vaga ficticia"
```

JSON esperado:

```json
[
  {
    "cargo": "Analista de Dados",
    "empresa": "Empresa Exemplo",
    "link": "https://example.com/jobs/123",
    "local": "Remoto",
    "descricao": "Python, SQL e dashboards.",
    "fonte": "JSON Manual",
    "status": "nova",
    "observacoes": "vaga ficticia"
  }
]
```

Links sao lidos apenas quando a pagina publica simples permite. Se houver bloqueio, login ou texto
ilegivel, o usuario deve abrir a pagina manualmente e colar a vaga.

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
cross-browser e ausencia de branding legado. O spec visual gera a serie `sotuhire-v1.7.1-web-*.png`
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
