# Frontend moderno

A v1.3.0 integra o frontend moderno do SotuHire em `apps/web`.

O app usa React, Vite, TypeScript, TanStack Router, TanStack Query, Tailwind CSS, Radix UI,
Recharts e lucide-react. Ele roda separado do Streamlit e consome a FastAPI local em `/api/v1`
quando o modo API Real está ativo.

## Como rodar

Suba a API local na raiz:

```bash
python scripts/run_api.py
```

Suba o frontend:

```bash
cd apps/web
npm install
npm run dev
```

Valide o frontend:

```bash
cd apps/web
npm run build
npm run lint
npm run typecheck
```

## Modos

- **Modo Demo:** usa mocks fictícios locais e permite navegar sem backend ativo.
- **Modo API Real:** usa `http://127.0.0.1:8787/api/v1`.

Configuração local:

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
para colar vaga manualmente, salvar link, importar arquivo, usar extensão assistida, radar público
e APIs oficiais quando disponíveis.

Ela não automatiza login, candidatura, LinkedIn, Gupy ou qualquer plataforma. A captura assistida
depende de ação manual do usuário.

O fluxo `AUTHENTICATED_BROWSER` existente no backend local tambem aparece nessa tela. Ele testa o
CDP local, abre um Chromium dedicado para login manual e exige confirmacao de uso autorizado antes
da coleta. Ele nao contorna CAPTCHA/checkpoint e nao envia candidatura.

## IA e Providers

A seção **IA e Providers** em Configurações é uma UI planejada para integração com backend local.
Ela mostra status, mascara a API key digitada e não salva segredos no frontend.

Endpoints planejados para v1.4.0:

```txt
GET /api/v1/settings/ai
POST /api/v1/settings/ai
POST /api/v1/settings/ai/test
DELETE /api/v1/settings/ai
GET /api/v1/settings/ai/status
```

Quando implementados, esses endpoints não devem retornar a chave para o frontend.

## Fronteira de responsabilidade

O frontend exibe estados, coleta inputs e chama a API. O backend/core continua responsável por:

- extração de currículo e vaga;
- Análise de Compatibilidade;
- ATS;
- Resume Tailor;
- GitHub Analyzer;
- tracker, métricas e persistência;
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
