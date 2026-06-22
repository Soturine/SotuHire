# Screen map

Este mapa define telas futuras sem prender layout. Lovable pode escolher a experiência
visual, desde que preserve dados, contratos e regras.

## 1. Landing / Home

- Objetivo: apresentar SotuHire, local-first, Match Engine, GitHub Analyzer e demo estática.
- Dados necessários: copy pública, links de docs, screenshots, release atual.
- Endpoint futuro: nenhum obrigatório.
- Estados vazios: não aplicável.
- Estados de erro: links indisponíveis devem degradar para navegação de docs.
- Liberdade visual: total para hero, cards, animações e CTA.
- Regras: não prometer que GitHub Pages roda backend.

## 2. Dashboard

- Objetivo: resumir perfil, análises recentes, vagas salvas e próximos passos.
- Dados necessários: perfil, métricas do tracker, análises recentes, gaps recorrentes.
- Endpoint futuro: `GET /api/v1/tracker/metrics`.
- Estados vazios: primeira análise ainda não executada.
- Estados de erro: API local indisponível ou storage não iniciado.
- Liberdade visual: cards KPI, charts, feed e atalhos.
- Regras: não calcular métricas críticas no frontend.

## 3. Upload/colagem de currículo

- Objetivo: receber currículo em texto ou arquivo.
- Dados necessários: texto bruto ou arquivo suportado.
- Endpoint futuro: `POST /api/v1/resume/extract`.
- Estados vazios: nenhum currículo carregado.
- Estados de erro: arquivo inválido, tipo não suportado, texto insuficiente.
- Liberdade visual: dropzone, editor, progresso e preview.
- Regras: não enviar dados a serviço externo sem consentimento explícito.

## 4. Perfil profissional

- Objetivo: mostrar perfil estruturado extraído e editável.
- Dados necessários: skills, experiências, formação, projetos, links e preferências.
- Endpoint futuro: `POST /api/v1/resume/extract`.
- Estados vazios: perfil não extraído.
- Estados de erro: baixa confiança de extração.
- Liberdade visual: abas, cards, tabelas ou timeline.
- Regras: diferenciar dado extraído de dado confirmado pela pessoa usuária.

## 5. Entrada de vaga

- Objetivo: receber descrição de vaga, link ou texto público.
- Dados necessários: texto da vaga e metadados opcionais.
- Endpoint futuro: `POST /api/v1/job/extract`.
- Estados vazios: nenhuma vaga informada.
- Estados de erro: vaga incompleta, descrição curta, fonte indisponível.
- Liberdade visual: editor, URL input, preview e checklist.
- Regras: não acessar área autenticada sem ação explícita da pessoa usuária.

## 6. Resultado de Match

- Objetivo: mostrar Match Score, Confidence, Evidence Score, gaps e ações seguras.
- Dados necessários: análise de currículo, vaga e evidências.
- Endpoint futuro: `POST /api/v1/match/analyze`.
- Estados vazios: currículo ou vaga ausente.
- Estados de erro: extração falhou, evidência insuficiente, baixa confiança.
- Liberdade visual: scorecards, breakdown, timeline, accordion e charts.
- Regras: Match Score real vem do backend/core.

## 7. ATS Review

- Objetivo: separar keywords presentes, seguras se verdadeiras e sem evidência.
- Dados necessários: currículo, vaga, keywords e match signals.
- Endpoint futuro: `POST /api/v1/ats/analyze`.
- Estados vazios: análise de match ainda não executada.
- Estados de erro: keywords insuficientes ou baixa confiança.
- Liberdade visual: listas, tags, heatmap e comparação.
- Regras: não sugerir keyword como fato sem evidência.

## 8. Resume Tailor

- Objetivo: sugerir ajustes seguros de currículo para a vaga.
- Dados necessários: perfil, vaga, ATS review e evidências.
- Endpoint futuro: `POST /api/v1/resume/tailor`.
- Estados vazios: sem análise ou sem evidências.
- Estados de erro: tentativa de gerar afirmação sem base.
- Liberdade visual: editor comparativo, sugestões aceitas/rejeitadas e checklist.
- Regras: nunca inventar experiência, credencial, cargo, empresa ou registro.

## 9. GitHub Analyzer

- Objetivo: analisar repositório público como evidência profissional.
- Dados necessários: URL ou owner/repo.
- Endpoint futuro: `POST /api/v1/github/repo/analyze`.
- Estados vazios: nenhum repositório informado.
- Estados de erro: repo privado, rate limit, URL inválida.
- Liberdade visual: scorecards, linguagens, evidências, arquivos e riscos.
- Regras: não exigir token para análise pública básica.

## 10. Portfolio Evidence

- Objetivo: consolidar projetos, links e evidências reutilizáveis.
- Dados necessários: GitHub, currículo, portfolio, memória local.
- Endpoint futuro: futuro endpoint de evidências.
- Estados vazios: nenhuma evidência conectada.
- Estados de erro: link indisponível ou evidência ambígua.
- Liberdade visual: biblioteca, tags e filtros.
- Regras: diferenciar evidência pública de dado privado/local.

## 11. Kanban de candidaturas

- Objetivo: acompanhar vagas por status.
- Dados necessários: jobs, status, fonte, datas, match e notas.
- Endpoint futuro: `GET/POST/PATCH /api/v1/tracker/jobs`.
- Estados vazios: nenhuma vaga salva.
- Estados de erro: conflito de atualização, job inexistente.
- Liberdade visual: board, listas, cards compactos e filtros.
- Regras: status e histórico devem persistir no backend/storage.

## 12. Application Intelligence / gráficos

- Objetivo: mostrar métricas e padrões das candidaturas.
- Dados necessários: métricas, requisitos, fontes, funil, gaps e timeline.
- Endpoint futuro: `GET /api/v1/tracker/metrics`, `/requirements`, `/funnel`, `/sources`.
- Estados vazios: dados insuficientes.
- Estados de erro: métricas indisponíveis ou storage corrompido.
- Liberdade visual: KPIs, barras, donut, funil, heatmap e tabelas.
- Regras: agregações oficiais devem vir da API.

## 13. Histórico

- Objetivo: listar análises, vagas e decisões anteriores.
- Dados necessários: eventos locais, análises e candidaturas.
- Endpoint futuro: futuro endpoint de histórico.
- Estados vazios: sem histórico.
- Estados de erro: falha ao carregar storage local.
- Liberdade visual: timeline, busca e filtros.
- Regras: respeitar privacidade e permitir limpeza local.

## 14. Configurações locais

- Objetivo: configurar provider opcional, storage, idioma e preferências.
- Dados necessários: status local, provider, flags e preferências.
- Endpoint futuro: futuro endpoint de settings.
- Estados vazios: configuração padrão.
- Estados de erro: provider indisponível, chave ausente, teste falhou.
- Liberdade visual: formulários, toggles e diagnóstico.
- Regras: segredos não devem aparecer em logs, screenshots ou frontend público.

## 15. Privacidade/local-first

- Objetivo: explicar onde os dados ficam e quais integrações são opcionais.
- Dados necessários: políticas do produto e status de storage.
- Endpoint futuro: nenhum obrigatório.
- Estados vazios: não aplicável.
- Estados de erro: não aplicável.
- Liberdade visual: página educativa, checklist e FAQ.
- Regras: não prometer privacidade absoluta se integração externa for ativada.

