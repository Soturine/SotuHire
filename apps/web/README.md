# SotuHire Web

Frontend moderno do SotuHire integrado em `apps/web` para a versão `v1.3.0`.

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

## Rodar localmente

Na raiz do repositório:

```bash
python scripts/run_api.py
```

Em outro terminal:

```bash
cd apps/web
npm install
npm run dev
```

Build e validação:

```bash
cd apps/web
npm run build
npm run lint
npm run typecheck
```

## Configuração da API

Crie um `.env` local se quiser trocar a URL padrão:

```env
VITE_SOTUHIRE_API_URL=http://127.0.0.1:8787/api/v1
```

O padrão do app é `http://127.0.0.1:8787/api/v1`.

## Modos

- **Modo Demo:** usa dados fictícios locais para explorar todas as telas.
- **Modo API Real:** consulta a FastAPI local em `/api/v1` e espera o envelope `{ ok, data, warnings, request_id }`.

O frontend não calcula score real, não move regra de negócio para o cliente e não salva segredos. A URL e o modo selecionados ficam apenas no estado da sessão aberta do app.

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

A seção **IA e Providers** em Configurações é uma UI planejada para integração segura com backend local. A chave é mascarada, não é persistida no frontend e deve ser tratada pelo backend quando os endpoints de configuração forem implementados.

Endpoints planejados para `v1.4.0`:

```txt
GET /api/v1/settings/ai
POST /api/v1/settings/ai
POST /api/v1/settings/ai/test
DELETE /api/v1/settings/ai
GET /api/v1/settings/ai/status
```

## Segurança e limites

## Navegador autenticado autorizado

A tela **Fontes e Captura** inclui o fluxo `AUTHENTICATED_BROWSER` existente no backend local:

- testa o CDP local em `http://127.0.0.1:9222`;
- abre um Chromium dedicado para login manual;
- exige confirmacao de uso autorizado antes de coletar;
- chama `/api/v1/sources/authenticated-browser/*` no modo API Real.

O fluxo nao automatiza login, nao contorna CAPTCHA/checkpoint e nao envia candidatura.

## Seguranca e limites

- Sem auto apply.
- Sem automação de LinkedIn, Gupy ou plataformas similares.
- Sem API keys em `localStorage`, `sessionStorage` ou bundle público.
- GitHub Pages continua estático/demo-oriented.
- Backend/core continuam responsáveis por regras, score e validações.
