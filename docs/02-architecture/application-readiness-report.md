# Application Readiness Report

`ApplicationReadinessReport` é o contrato auditável produzido na etapa 5 do Lab. Ele separa score determinístico de qualquer explicação opcional de IA e nunca usa “probabilidade de entrevista”.

O relatório contém score e explicação, cobertura de evidências e requisitos, dimensões por fonte, strengths, bloqueadores, informações ausentes, riscos de afirmação sem suporte, edições recomendadas, snippets seguros, plano preliminar, warnings, metadados do provider e evidências usadas.

As dimensões são Currículo, Formação, Experiência, Competências, Projetos, Portfólio, Lattes/produção acadêmica, Certificações, Registros profissionais, Idiomas, GitHub e Requisitos da vaga. Itens não aplicáveis são removidos do denominador; GitHub fica `not_applicable` fora de contextos onde seja relevante.

A interface apresenta uma única análise consolidada em três perspectivas: Estrutura e ATS, Narrativa e posicionamento, e Evidências e diferenciais. Isso descreve a leitura do mesmo relatório; não simula agentes nem chamadas paralelas.
