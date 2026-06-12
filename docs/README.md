# Documentação do SotuHire

Esta pasta reúne a documentação completa do SotuHire. Ela foi organizada por áreas para evitar um único README gigante e para deixar o projeto com cara de produto/engenharia, não só de experimento com IA.

## Mapa dos documentos

### 00 - Auditoria

- [documentation-audit.md](00-audit/documentation-audit.md): auditoria dos documentos antigos, problemas encontrados e decisões tomadas na reconstrução.

### 01 - Produto

- [vision.md](01-product/vision.md): visão geral, problema, proposta de valor e posicionamento do SotuHire.
- [mvp-scope.md](01-product/mvp-scope.md): escopo por MVP, o que entra e o que não entra.
- [user-stories.md](01-product/user-stories.md): histórias de usuário e critérios de aceite.
- [roadmap.md](01-product/roadmap.md): evolução planejada por versões.

### 02 - Arquitetura

- [overview.md](02-architecture/overview.md): arquitetura modular inicial.
- [folder-structure.md](02-architecture/folder-structure.md): estrutura de pastas recomendada.
- [data-flow.md](02-architecture/data-flow.md): fluxo de dados do currículo até o relatório.
- [architecture-decisions.md](02-architecture/architecture-decisions.md): decisões arquiteturais e motivos.

### 03 - Regras de negócio

- [matching-rules.md](03-business-rules/matching-rules.md): regras para score, classificação e recomendação.
- [ats-rules.md](03-business-rules/ats-rules.md): critérios de análise ATS.
- [job-filtering.md](03-business-rules/job-filtering.md): regras para filtrar vagas incompatíveis.

### 04 - IA

- [prompting.md](04-ai/prompting.md): estratégia de prompts, papéis e limites da IA.
- [structured-output-schema.md](04-ai/structured-output-schema.md): schema JSON esperado para respostas do modelo.
- [evaluation.md](04-ai/evaluation.md): como avaliar qualidade das respostas de IA.

### 05 - Fontes de vagas

- [job-sources.md](05-data-sources/job-sources.md): fontes formais de vagas e abordagem segura.
- [hidden-jobs-radar.md](05-data-sources/hidden-jobs-radar.md): radar de posts, indicações e oportunidades informais.
- [compliance-and-ethics.md](05-data-sources/compliance-and-ethics.md): limites práticos, legais e éticos.

### 06 - Engenharia

- [clean-code-solid.md](06-engineering/clean-code-solid.md): como aplicar Clean Code e SOLID sem overengineering.
- [qa-testing.md](06-engineering/qa-testing.md): estratégia de QA e testes automatizados.
- [avoid-overengineering.md](06-engineering/avoid-overengineering.md): o que evitar no MVP.
- [security-privacy.md](06-engineering/security-privacy.md): segurança, privacidade e tratamento de currículo.

### 07 - Desenvolvimento

- [setup.md](07-development/setup.md): configuração local.
- [contributing.md](07-development/contributing.md): guia de contribuição.
- [commands.md](07-development/commands.md): comandos úteis.
