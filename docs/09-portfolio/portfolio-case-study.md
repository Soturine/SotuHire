# Case study — coordenar carreira sem retirar controle

## Problema

Perfil, currículo, portfólio, oportunidades e resultados viviam como módulos conectados, mas não
formavam um estado único nem uma boundary consistente para ações.

## Decisões

- graph relacional em SQLite para manter deployment local simples;
- Career State determinístico e provider apenas explicativo;
- tool registry fechado e todo write importante como ProposedAction;
- preview, impacto, approval, audit e undo como contrato, não detalhe de UI;
- GitHub como fonte opcional em uma arquitetura multidisciplinar.

## Trade-offs

MCP foi adiado; graph visualization avançada e export de portfólio não justificavam risco no gate.
Compatibilidade JSON permanece até migração segura. O resultado é menos automação de terceiros e
mais rastreabilidade local, sem alegar aumento causal de contratação.
