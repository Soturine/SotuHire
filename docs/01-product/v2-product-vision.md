# Visão de produto v2

O SotuHire v2 representa o estado da carreira e coordena próximas ações sob aprovação humana. Ele
combina Perfil Universal, Evidence Graph, portfólio, trajetória acadêmica/profissional,
oportunidades, candidaturas, entrevistas, tarefas, outcomes, objetivos e preferências.

## Problema

Ferramentas de carreira costumam produzir documentos ou scores isolados. O usuário ainda precisa
lembrar por que uma recomendação apareceu, qual evidência a sustenta e o que mudou desde a última
análise. Quando IA é adicionada sem boundary, sugestão e execução podem se confundir.

A v2 cria continuidade entre informação, decisão e resultado. O produto registra origem e estado de
revisão, calcula prioridades por regras e mantém cada escrita importante atrás de preview e
aprovação.

## Para quem serve

O modelo é multiárea: software, engenharia, saúde, direito, pesquisa, educação, design, artes,
administração, serviços, carreiras técnicas, concursos, início ou transição. GitHub é uma fonte útil
quando aplicável, não uma exigência para possuir portfólio.

## Proposta de valor

O SotuHire deve ajudar a responder:

- o que está confirmado sobre minha trajetória;
- quais informações ainda precisam de revisão;
- onde estão lacunas relevantes para meu objetivo;
- qual próximo passo é pequeno, explicável e útil;
- o que uma proposta mudará antes de eu aprovar;
- como desfazer uma escrita local quando suportado;
- quais decisões e outcomes já ocorreram.

## Divisão de responsabilidades

Serviços determinísticos calculam estado, regras e validações. IA opcional observa, compara,
explica, planeja e redige. O usuário confirma evidências e aprova ações. Application services
executam efeitos locais e auditáveis.

```text
dados revisados → estado determinístico → recomendação explicável
                                      → proposta → aprovação → execução local
```

## Princípios

1. local-first antes de integração externa;
2. evidência antes de claim;
3. confiança não substitui revisão;
4. explicação antes de ação;
5. proposta não é execução;
6. aprovação é individual;
7. audit e undo preservam histórico;
8. provider não controla regra de negócio;
9. sem auto-apply, login ou envio automático;
10. limitações aparecem na documentação e na UI.

## O que significa sucesso

Sucesso não é “mais automação”. É reduzir trabalho perdido e decisões opacas: menos informação
duplicada, melhor rastreabilidade, próximas ações compreensíveis e materiais sustentados por fatos.

Métricas de produto devem observar utilidade e segurança — propostas aceitas/rejeitadas, stale,
undo, cobertura e outcomes — sem converter correlação em promessa causal.

## Limites atuais

MCP não é exposto na v2.0. O produto não envia candidatura, mensagem ou documento; não faz login,
pagamento ou bypass; não publica portfólio automaticamente. Visualização avançada do graph, export
dedicado do portfólio e i18n integral das telas históricas permanecem pós-v2.

## Leitura relacionada

- [Primeiros passos](../05-user-guide/getting-started.md)
- [Jornada de carreira e aprovações](../05-user-guide/career-workflow.md)
- [Evidence Graph](../02-architecture/evidence-graph.md)
- [Human-Approved Career Copilot](../02-architecture/human-approved-copilot.md)
- [Fluxo de dados](../02-architecture/data-flow.md)
- [Roadmap pós-v2](roadmap.md)
