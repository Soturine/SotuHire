# SotuHire Web

Frontend moderno do SotuHire em `apps/web` para a versão `v1.9.2`.

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

## Rodar Localmente

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
npm ci
npm run dev
```

Build e validação:

```powershell
cd apps/web
npm run build
npm run lint
npm run typecheck
npm run test:unit
npm run test:e2e
npm run test:e2e:cross-browser
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

O frontend não calcula score real, não move regra de negócio para o cliente e não salva segredos. A URL e o modo selecionados ficam apenas no estado da sessão aberta do app.

## Dados, Backup e Restauração

A rota `/privacy` reúne o painel de confiabilidade dos dados. No modo API Real, ela permite:

- executar o data health read-only;
- revisar versão do schema, contagens, warnings e erros;
- criar backup ou export portátil com manifesto/checksums;
- listar e baixar arquivos mantidos pela API local;
- validar um restore sem alterar dados;
- aplicar o restore somente após digitar `RESTAURAR` e confirmar o diálogo final.

Endpoints usados:

```txt
GET  /api/v1/data/health
GET  /api/v1/data/backups
POST /api/v1/data/backups
GET  /api/v1/data/backups/{archive_name}
POST /api/v1/data/restore
```

A API cria e restaura apenas arquivos do diretório local gerenciado `data/backups`; o navegador não recebe caminhos absolutos. Antes de sobrescrever dados, o backend cria um backup de segurança. Arquivos de backup/export excluem categorias secretas, chaves detectadas em stores textuais, cookies, tokens e storage da extensão.

O modo Demo simula esses estados para demonstração visual: ele não cria, baixa ou restaura arquivos. A documentação operacional está em [Backup, restauração e data health](../../docs/02-architecture/backup-restore-and-data-health.md).

## Telas

- Home/Dashboard
- Currículo
- Vaga
- Análise de Compatibilidade
- Análise ATS
- Ajuste de Currículo
- Análise de GitHub
- Radar de Vagas
- Perfil Profissional Universal
- Acadêmico / Lattes
- Candidaturas
- Inteligência de Candidaturas
- Fontes e Captura
- Configurações
- Privacidade, Data Health, Backup e Restauração

## IA e Providers

A seção **IA e Providers** em Configurações usa endpoints reais da API local:

```txt
GET /api/v1/settings/ai
GET /api/v1/settings/ai/status
GET /api/v1/settings/ai/providers
GET /api/v1/settings/ai/models?provider=gemini
GET /api/v1/settings/ai/models?provider=openai
POST /api/v1/settings/ai/models/refresh
POST /api/v1/settings/ai
POST /api/v1/settings/ai/test
DELETE /api/v1/settings/ai
```

Na v1.9.4, a UI mostra presets **Local seguro**, **IA básica**, **IA completa** e **Personalizado**. Gemini e OpenAI usam catálogo de modelos, botão para obter chave oficial e secret salvo apenas no backend local.

A chave digitada é enviada somente para o backend local e limpa do estado do componente após salvar. Ela não é persistida em `localStorage`, `sessionStorage` ou bundle público. A API nunca retorna a chave; retorna apenas provider, modelo, `configured`, `status`, toggles, warnings e `updated_at`.

## IA e Qualidade

A rota `/ai-quality` funciona em Demo e API Real e organiza Resumo, Providers, Prompts, Benchmarks, Feedback, Resultados profissionais e Privacidade. Ela mostra somente metadados seguros, exige tamanho de amostra nas comparações e oferece criação/remoção de feedback e eventos manuais de outcome. O empty state padrão é “Não há execuções suficientes para gerar métricas confiáveis.”

Estados exibidos na UI:

```txt
IA desativada
Provider local
Provider configurado
Provider não configurado
Analisando com IA
Fallback local
Limite/erro do provider
Timeout do provider
Chave inválida
```

## Perfil Profissional e Lattes

A rota `/profile` implementa o Perfil Profissional Universal:

- edição de dados básicos;
- itens com origem, evidência, confiança e confirmação do usuário;
- filtro por tipo;
- edição inline de título, domínio e evidência;
- importação de texto de currículo, portfólio, certificados e notas;
- aba **Acadêmico / Lattes** para texto colado do Currículo Lattes;
- extração de formação, pesquisa, publicações, extensão, docência, monitoria, eventos, prêmios, bolsas e produção técnica/artística;
- revisão de itens extraídos antes de adicionar ao Perfil.

Endpoints usados:

```txt
GET/PUT /api/v1/profile
POST /api/v1/profile/items
PATCH/DELETE /api/v1/profile/items/{id}
POST /api/v1/profile/import-text
POST /api/v1/profile/import-lattes
POST /api/v1/profile/lattes/draft
POST /api/v1/profile/lattes/confirm
POST /api/v1/profile/deduplicate
GET /api/v1/profile/context
```

O frontend não confirma automaticamente itens vindos de IA/fallback e não envia segredos ao backend. O Lattes é aceito por texto colado; o app não faz login, scraping autenticado ou crawler do Lattes.

## Fontes, Captura e Extensão

A tela **Fontes e Captura** inclui importadores, Caixa de Entrada, Diretório de Fontes, fluxo da extensão assistiva e o fluxo `AUTHENTICATED_BROWSER` existente no backend local:

- testa o CDP local em `http://127.0.0.1:9222`;
- abre um Chromium dedicado para login manual;
- exige confirmação de uso autorizado antes de coletar;
- chama `/api/v1/sources/authenticated-browser/*` no modo API Real.

O painel **Extensão Local** consulta `/api/v1/extension/status`, `/api/v1/extension/captures` e `/api/v1/extension/context`. Ele mostra capturas salvas pela Local Companion API, permite enviar para Vaga/Editais/GitHub/Candidaturas e gera candidatos revisáveis para o Perfil.

Capturas com `kind=public_exam` podem abrir `/public-exams?capture_id=...` e virar rascunho revisável. O frontend não expõe API key nem recebe Perfil completo da extensão.

A extensão não acessa a API key do app, não coleta cookies, tokens, sessão, headers ou storage de terceiros e não automatiza candidatura.

## Radar de Vagas

A tela `/radar` permite:

- criar wishlist com cargos, skills, locais, modelo de trabalho e score mínimo;
- criar rascunho de wishlist a partir de texto livre com IA/local;
- usar Perfil Profissional Universal como contexto opcional;
- adicionar fonte RSS/Atom pública;
- registrar API oficial planejada via adapter seguro;
- rodar Radar manualmente;
- revisar resultados, evidências, lacunas e alertas;
- criar e pausar agendamentos locais;
- executar agendamento agora;
- consultar histórico de runs agendadas;
- revisar notificações locais/in-app.

Agendamentos rodam somente enquanto a API local está aberta. Eles respeitam quiet hours, cooldown, Perfil Profissional Universal opcional e revisão humana. O frontend não agenda auto-apply, não coleta segredo e não salva candidatura final sem ação do usuário.

## Kanban e Responsividade

O Kanban de Candidaturas usa status reais do backend, drag-and-drop visual, rollback quando a API falha e select de status como alternativa para teclado/mobile. O teste responsivo valida:

```txt
Mobile: 390x844
Tablet: 768x1024
Desktop: 1440x1000
```

## Testes e Screenshots

```powershell
cd apps/web
npm run test:unit
npm run test:e2e
```

O Playwright cobre Home, Dashboard, fluxo guiado, demos de análise, IA Settings, Perfil/Lattes, Fontes e Captura, Kanban, cross-browser em Chromium/Firefox/WebKit e ausência de branding legado público.

`scripts/capture_web_walkthrough.py` gera screenshots e GIF atuais em:

```txt
docs/assets/screenshots/
```

## Segurança e Limites

- Sem auto-apply.
- Sem automação de LinkedIn, Gupy ou plataformas similares.
- Sem login ou scraping autenticado do Lattes.
- Sem inscrição automática em concursos ou editais.
- Sem API keys em `localStorage`, `sessionStorage` ou bundle público.
- Restore HTTP em dry-run por padrão e aplicação com confirmação explícita.
- Caminhos absolutos do diretório de dados não são enviados ao frontend.
- GitHub Pages continua estático/demo-oriented.
- Backend/core continuam responsáveis por regras, score e validações.
- Streamlit permanece disponível como modo legado/dev/local debug.
