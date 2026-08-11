# Demo SotuHire v2 — 3 a 5 minutos

Esta demo é para recrutadores, pessoas desenvolvedoras e avaliadores de produto que querem entender
rapidamente como o SotuHire coordena carreira sem transformar IA em autoridade. Use somente a
persona fictícia preparada para a demonstração.

1. **Problema (20s):** perfil, portfólio e candidaturas fragmentados não revelam prioridade nem a
   evidência ausente.
2. **Cockpit (30s):** mostrar estado, cobertura, candidatura, entrevista e Next Best Action com
   razão verificável — o cálculo é determinístico.
3. **Evidence Inbox (35s):** um documento fictício produz `candidate`; confirmar um item e rejeitar
   outro para demonstrar que proveniência não equivale a verdade.
4. **Graph e Portfólio (30s):** um projeto e uma skill têm edge revisável; explicar por que SQLite
   foi preferido a um serviço de graph e por que GitHub é só uma fonte opcional.
5. **Copilot (40s):** abrir o drawer, inspecionar contexto mínimo e criar uma Proposed Action; o
   modelo não escolhe tools nem escreve diretamente.
6. **Approval Queue (40s):** comparar before/after, evidências, impacto e risco; aprovar
   individualmente e executar pelo application service.
7. **Undo e audit (25s):** desfazer a tarefa local e mostrar que execução e undo permanecem no
   histórico.
8. **Jornada de candidatura (30s):** oportunidade → currículo → Tracker → entrevista → outcome,
   sempre com candidatura e envio manuais.
9. **Segurança e encerramento (20s):** provider opt-in, dados sensíveis omitidos, conteúdo importado
   não confiável e MCP não exposto na v2.0.

As três decisões técnicas memoráveis são: **determinístico antes de IA**, **proposta antes de
escrita** e **SQLite local antes de infraestrutura distribuída**. Nunca mostre chaves, dados pessoais
ou a fixture como resultado de uso real.

Para aprofundar após a demo, use o [case study](portfolio-case-study.md) e a
[arquitetura do Copilot](../02-architecture/human-approved-copilot.md).
