# Evidence Graph

O Evidence Graph é a camada que transforma informações dispersas de carreira em fatos e relações
revisáveis. Ele existe para responder não apenas “o que sabemos sobre esta pessoa?”, mas também
“de onde veio essa informação?”, “ela foi confirmada?” e “qual decisão depende dela?”.

O graph da v2.0 usa SQLite. Não há Neo4j, serviço externo ou sincronização automática com uma
nuvem. Essa escolha mantém instalação, backup, auditoria e recuperação compatíveis com o princípio
local-first do SotuHire.

## Objetivo

Currículos, Lattes, portfólios, repositórios, vagas e entrevistas descrevem a mesma trajetória com
formatos e níveis de confiança diferentes. Copiar tudo diretamente para o Perfil Universal faria
uma inferência parecer fato. O Evidence Graph introduz uma fronteira explícita entre:

- conteúdo capturado ou inferido;
- evidência revisada pelo usuário;
- relações entre evidências;
- contexto autorizado para análises e propostas;
- histórico preservado quando algo muda ou deixa de ser válido.

O graph não substitui o currículo, o Tracker ou o portfólio. Ele conecta esses domínios por IDs,
origem e estado de revisão.

## Nós

`evidence_nodes` representa entidades da trajetória profissional. A v2.0 reconhece 27 tipos:
pessoa, perfil, experiência, educação, projeto, skill, conhecimento, ferramenta, certificação,
registro profissional, publicação, pesquisa, curso, prêmio, evento, voluntariado, extensão,
docência, item de portfólio, repositório, documento, oportunidade, requisito, candidatura,
entrevista, outcome e objetivo de carreira.

Cada nó possui, no mínimo:

- identificador estável;
- tipo e título;
- resumo e payload estruturado;
- `source_refs` para a origem;
- estado de revisão;
- confiança numérica separada da revisão humana;
- timestamps e, quando aplicável, `stale_at`;
- marcação `sensitive` para dados que exigem tratamento restrito.

Um nó pode existir como candidato sem participar de decisões autoritativas. Isso permite importar e
comparar dados antes de incorporá-los ao perfil confirmado.

## Relações

`evidence_edges` registra relações tipadas, como projeto que demonstra uma skill, certificação que
sustenta uma competência, oportunidade que exige um requisito ou outcome associado a uma
candidatura. A relação tem identidade, proveniência, confiança e revisão próprias.

Confirmar um nó não confirma automaticamente suas relações. Por exemplo: confirmar que um projeto
existe não prova, sozinho, que ele demonstra uma competência específica. Essa edge continua
`candidate` até ser revisada.

## Proveniência

`source_refs` indica onde a informação foi obtida: entrada manual, documento importado, Lattes,
GitHub, extensão, oportunidade ou outro registro local. `evidence_refs` aponta para fatos do próprio
graph que sustentam uma relação ou recomendação.

Proveniência não significa verdade automática. Ela torna a afirmação rastreável e permite que a UI
responda “por que isto está aqui?”. Quando a fonte original muda, o sistema pode identificar os
consumidores afetados sem apagar o histórico anterior.

## Estados de revisão

Os estados têm semântica de produto, não apenas de interface:

| Estado | Significado | Uso em decisões |
| --- | --- | --- |
| `candidate` | capturado, extraído ou inferido; ainda precisa de revisão | não deve ser tratado como fato confirmado |
| `confirmed` | revisado e aceito pelo usuário | pode alimentar Career State, Match e contexto autorizado |
| `rejected` | revisado e recusado | preservado para auditoria, mas excluído como fato |
| `stale` | já foi relevante, porém sua dependência mudou ou precisa ser reconfirmada | não deve sustentar nova execução sem revisão |

Rejeitar não apaga. Manter a decisão evita que a mesma inferência reapareça silenciosamente em uma
nova importação.

## Confiança

Confiança expressa a força estimada do dado ou da relação. Ela nunca substitui o estado de revisão.
Uma inferência com confiança alta ainda é `candidate`; um fato confirmado pode ter confiança menor
quando a fonte é incompleta.

O Career State separa cobertura de dados, confiança das regras e, quando existe IA externa,
confiança do provider. Isso impede que um score de modelo seja apresentado como certeza do sistema.

## Dados sensíveis

Registros profissionais podem conter número, jurisdição, categoria e validade. Esses nós usam
`sensitive=true`. O número do registro não entra em contexto externo por padrão e não deve aparecer
em busca, prompt ou export público sem seleção explícita.

O mesmo princípio se aplica a anexos e dados pessoais: o graph referencia metadata e origem; ele
não concede autorização implícita para compartilhamento.

## Evidence Inbox

A Evidence Inbox é a interface de revisão dos nós candidatos. Nela, o usuário inspeciona tipo,
resumo, origem e confiança antes de confirmar ou rejeitar. A Inbox é deliberadamente anterior ao
Career State: dados não revisados não devem alterar prioridades como se fossem verdadeiros.

A Inbox também é o lugar correto para explicar divergências e duplicatas. Ela não oferece uma ação
global que confirme tudo sem inspeção.

## Deduplicação

Merge automático só é seguro quando existe identidade forte e verificável. Título parecido,
descrição semelhante ou sugestão de IA não bastam. Nos demais casos, os candidatos permanecem
separados para revisão.

Ao consolidar itens, o sistema deve preservar referências às fontes e não transformar duas origens
em uma alegação mais forte do que ambas suportam. A v2.0 não oferece um editor visual avançado de
merge; as operações estruturadas permanecem API-first.

## Stale

Um nó ou relação fica stale quando a informação que o sustentava mudou, expirou ou foi substituída.
Stale preserva o registro anterior, mas impede que ele seja usado silenciosamente como contexto
atual. O mesmo dependency hash é usado na fronteira de propostas do Copilot: se o estado muda entre
preview e aprovação, a proposta também deixa de ser executável.

## Integração com Career State

O Career State lê evidências confirmadas e os demais stores SQLite relevantes para produzir um
snapshot determinístico. O graph contribui com cobertura, lacunas, projetos, competências,
formação, portfólio e objetivos. Renderizar uma página não grava snapshot; persistência de estado é
uma operação explícita.

O fluxo é:

```text
fontes → candidate → revisão → confirmed → Career State → Next Best Actions
```

## Integração com Match e Copilot

Match compara requisitos da oportunidade com evidências confirmadas. Ausência de evidência é
tratada como lacuna, não como prova de ausência de competência. O Copilot usa apenas o recorte
necessário para explicar ou propor uma ação e registra quais referências foram consideradas.

Conteúdo de uma vaga, PDF, README ou página capturada continua sendo dado não confiável. Ele pode
originar um candidato, mas não invocar tools nem contornar aprovação.

## Persistência e source of truth

Na v2.0, `evidence_nodes` e `evidence_edges` no SQLite schema 8 são o source of truth do graph.
JSON/JSONL legado pode participar de compatibilidade, fixture ou export, mas não recebe dual-write
dos novos domínios v2.

Backups e migrações seguem os mecanismos gerais do SQLite. O histórico de revisão, stale e
proveniência deve sobreviver a upgrade e restore.

## Exemplo simples

```text
Projeto Aurora (confirmed)
  ├─ project_demonstrates_skill → Python (candidate)
  └─ project_uses_tool → FastAPI (confirmed)

Fonte do projeto: currículo importado e revisado
Fonte da relação com Python: inferência aguardando confirmação
```

O projeto pode alimentar o portfólio, enquanto a primeira relação ainda não pode sustentar uma
afirmação de competência confirmada.

## Limites

- não há banco de graph externo;
- não há confirmação automática por confiança alta;
- não há merge sem identidade forte;
- não há publicação automática de evidências ou portfólio;
- não há editor visual completo de relações na v2.0;
- o graph não substitui validação oficial de registros, diplomas ou certificações.

## Links relacionados

- [Human-Approved Career Copilot](human-approved-copilot.md)
- [Portfólio e evidência acadêmica/profissional](portfolio-and-academic-evidence.md)
- [Fluxo de dados v2](data-flow.md)
- [Guia da jornada de carreira](../05-user-guide/career-workflow.md)
- [Migração e recuperação v2](../06-engineering/v2-migration-and-recovery.md)
- [Threat model v2](../06-engineering/v2-security-threat-model.md)
