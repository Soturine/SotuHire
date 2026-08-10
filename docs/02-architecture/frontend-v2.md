# Frontend v2 e design system

O frontend v2 organiza o SotuHire por jornada de carreira, não por uma coleção de ferramentas
isoladas. Career Cockpit, Evidence Inbox, Portfólio, Approval Queue e Copilot contextual formam a
entrada para os domínios existentes de perfil, currículo, oportunidades, candidaturas e entrevistas.

## Princípios

- mostrar estado e próxima decisão antes de detalhes técnicos;
- distinguir claramente Demo de API Real;
- manter writes atrás de preview e aprovação;
- usar progressive disclosure para não exibir todo o sistema de uma vez;
- oferecer teclado, tema e responsividade como comportamento básico;
- não simular dados reais quando a API está vazia ou indisponível.

## Career Cockpit

O Cockpit substitui o dashboard de scores fixos por Career State e Next Best Actions. Ele apresenta
cobertura, trajetória, aprovações, lacunas e próximos passos com razões rastreáveis.

Cards não concedem autoridade ao provider: números autoritativos vêm do backend determinístico ou
são rotulados como demonstração fictícia.

## Superfícies v2

| Rota | Responsabilidade |
| --- | --- |
| `/dashboard` | Career Cockpit e prioridades |
| `/evidence` | revisão da Evidence Inbox |
| `/portfolio` | trabalhos multidisciplinares e fontes |
| `/approvals` | propostas, preview, risco, aprovação e undo |
| drawer Copilot | contexto da página, planos e propostas |

As demais rotas continuam acessíveis por jornada: perfil e materiais, oportunidades, candidaturas,
entrevistas, plano de carreira, integrações e configurações.

## Camada de API

O client v2 deriva `/api/v2` da mesma base loopback usada pelo modo API Real. Query keys incluem
modo e base URL para evitar cache de outra origem. Demo usa fixtures fictícias e não faz escrita no
backend real.

Tipos de evidence, portfolio, Career State e proposals ficam agrupados no feature client do
Copilot, enquanto contratos históricos continuam compatíveis com `/api/v1`.

## Copilot persistente

O drawer contextual acompanha a navegação e apresenta a finalidade do contexto. Abrir o Copilot não
executa ação. Propostas aparecem na Approval Queue, onde before/after e impacto podem ser revisados.

Em telas pequenas, o drawer usa comportamento modal com foco e Escape. A interface não inclui um
botão global de aprovação.

## Command Palette e busca

`Ctrl/Cmd+K` abre a Command Palette. Ela combina navegação com busca universal local sobre os
domínios suportados. A busca respeita modo/base URL e não cria um índice externo.

## Design system

Tokens semânticos definem background, surface, text, muted, border, primary, accent, warning,
danger e success. Componentes consomem o papel do token em vez de cores literais, permitindo tema
claro, escuro e preferência do sistema.

Tipografia, spacing, radius e sombras mantêm hierarquia consistente. Cards de decisão privilegiam
título, motivo, estado e ação; metadata secundária fica abaixo ou em disclosure.

## Identidade visual

A identidade v2 usa contraste sóbrio, acentos para decisão e gráficos de trajetória em vez de
gamificação. Cor nunca é o único sinal de estado: labels e texto acompanham candidate, confirmed,
rejected, stale, pending, approved e executed.

## i18n

Shell e superfícies v2 usam catálogo pt-BR/en-US tipado. Preferência é persistida e aplicada sem
reload. Conteúdo histórico ainda possui trechos pt-BR e segue migração incremental; a v2.0 não
declara tradução integral retroativa.

## Responsividade

A matriz cobre 360, 390, 768, 1024, 1440 e 1920 px. Layouts evitam overflow no documento e
transformam navegação/drawers conforme o espaço. Application Lab e Resume Studio também são
verificados em zoom de 200%.

## Acessibilidade

Headings seguem hierarquia de página, drawers e diálogos possuem semântica, foco e Escape, e ações
principais têm nome acessível. Teclado cobre Command Palette e jornada v2. Esses testes reduzem
regressões, mas não constituem certificação WCAG formal.

## Onboarding e ajuda

O onboarding explica idioma/tema, local-first, perfil, importação opcional, IA, extensão,
oportunidades e approval boundary. Ajuda contextual aponta para a responsabilidade da tela sem
substituir a documentação detalhada.

## Estados vazios e erros

API Real vazia mostra orientação de próxima ação e não injeta personas demo. Falhas de provider são
tipadas e preservam fallback quando existe. Erros de pairing ou API indicam recuperação sem pedir ao
usuário que exponha token ou chave no navegador.

## Movimento

Movimento comunica abertura, mudança de estado ou confirmação. `prefers-reduced-motion` reduz
animações e transições. A interface evita efeitos decorativos que atrasem revisão de propostas.

## Limites

- visualização avançada do graph permanece API-first;
- timeline histórica completa ainda não possui explorer dedicado;
- i18n histórico não está totalmente migrado;
- não há publicação automática de portfólio;
- screenshots documentam fixtures demo, não uso real de provider ou candidatura.

## Links relacionados

- [Guia da jornada](../05-user-guide/career-workflow.md)
- [Human-Approved Career Copilot](human-approved-copilot.md)
- [Frontend API Layer](frontend-api-layer.md)
- [I18n e tema](i18n-and-theme.md)
- [Ajuda contextual](help-system.md)
- [Threat model v2](../06-engineering/v2-security-threat-model.md)

