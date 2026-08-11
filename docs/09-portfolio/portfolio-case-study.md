# Case study — coordenar carreira sem retirar controle

## Contexto e problema

Dados de carreira raramente vivem em um único lugar. Perfil, currículo, Lattes, portfólio,
repositórios, vagas, candidaturas, entrevistas e resultados usam estruturas diferentes e envelhecem
em ritmos diferentes. Nas primeiras etapas do SotuHire, esses módulos já se conectavam, mas a
experiência ainda dependia de o usuário reconstruir mentalmente o contexto: qual informação estava
confirmada, por que uma recomendação apareceu e o que mudaria ao seguir a sugestão.

Adicionar apenas um chat de IA não resolveria essa fragmentação. Um modelo poderia resumir os
textos, mas continuaria sem um source of truth claro, sem distinguir inferência de fato e sem uma
boundary confiável entre sugestão e execução. Pior: uma vaga, PDF ou README poderia conter
instruções não confiáveis e influenciar uma automação com acesso excessivo.

A v2 reformulou o problema como coordenação de estado. O sistema precisava representar evidências,
derivar prioridades de maneira reproduzível e permitir que um Copilot planejasse sem retirar do
usuário o controle de cada escrita relevante.

## Objetivos do projeto

O produto foi orientado por seis objetivos:

- **local-first:** perfil e histórico começam no dispositivo, com integrações externas opcionais;
- **multiárea:** GitHub pode ser útil, mas pesquisa, ensino, design, engenharia, saúde, artes e
  carreiras técnicas precisam da mesma representatividade;
- **evidence-first:** uma afirmação deve apontar para uma origem e um estado de revisão;
- **explicável:** prioridade, confiança e impacto precisam ser inspecionáveis;
- **aprovação humana:** plano e proposta não equivalem a autorização de escrita;
- **sem auto-apply:** candidatura, e-mail, login, formulário, CAPTCHA e pagamento permanecem fora
  do produto.

O objetivo não era prometer melhor contratação. Era tornar o processo local mais coerente,
rastreável e seguro.

## Restrições e princípios

Privacidade e operação simples limitaram escolhas arquiteturais. O produto deve funcionar sem
provider externo, sem servidor de graph e sem infraestrutura distribuída. IA não pode inventar
experiências, resultados ou qualificações, e dados sensíveis não devem entrar em contexto externo
por conveniência.

Também havia uma base instalada: APIs, tabelas e stores anteriores tinham consumidores reais. Uma
migração agressiva poderia quebrar compatibilidade ou apagar histórico. Por isso, novos domínios v2
adotaram SQLite como writer único, enquanto compatibilidade legada foi preservada onde ainda era
necessária e explicitamente documentada.

Esses princípios aparecem no [fluxo de dados v2](../02-architecture/data-flow.md) e no
[threat model](../06-engineering/v2-security-threat-model.md).

## Arquitetura escolhida

O frontend React/TypeScript apresenta a jornada e consome uma API FastAPI local. Pydantic define
contratos estritos nas boundaries. SQLite schema 8 persiste Evidence Graph, portfólio, snapshots de
Career State, planos, propostas, execuções e audit.

O [Evidence Graph](../02-architecture/evidence-graph.md) representa 27 tipos de nós e relações
tipadas. Ele registra proveniência, confiança e revisão sem exigir Neo4j. Evidências confirmadas e os
demais stores locais alimentam o Career State, calculado deterministicamente. O Next Best Action
Engine ordena candidatos por regras transparentes.

O [Human-Approved Career Copilot](../02-architecture/human-approved-copilot.md) lê um recorte mínimo
desse estado, cria planos e prepara Proposed Actions. O Tool Registry mantém uma allowlist com
schemas, categoria, risco e necessidade de aprovação. Um application service só executa a proposta
depois de preview, aprovação individual e nova validação de status, expiração e dependency hash.

O Provider Router oferece caminho local, Gemini, OpenAI e endpoints locais compatíveis como Ollama
e LM Studio. Providers ajudam em extração, explicação ou draft; nunca calculam o estado oficial nem
escolhem uma tool.

## Desafios técnicos mais relevantes

### Proveniência não é confirmação

Saber que um dado veio de um currículo ou repositório não o torna verdadeiro ou atual. A solução foi
separar `candidate`, `confirmed`, `rejected` e `stale`. Confirmar um projeto não confirma
automaticamente a edge que afirma que ele demonstra determinada skill. Essa distinção reduz claims
não suportadas e permite que a Evidence Inbox seja uma etapa real, não decorativa.

### Deduplicação sem destruir contexto

Título parecido não é identidade. Merge automático exige sinal forte; os demais candidatos ficam
separados para revisão. Ao consolidar, as referências de origem precisam sobreviver. O trade-off é
mais trabalho humano em casos ambíguos, em troca de menos junções incorretas e melhor auditoria.

### Snapshots, stale e concorrência

Uma proposta pode ser correta no momento do preview e inadequada minutos depois. Career State gera
um dependency hash; se o estado muda, a Proposed Action fica stale. Compare-and-set protege
transições concorrentes, e idempotency keys contêm retries. Isso evita que aprovação antiga seja
reutilizada sobre contexto novo.

### Source of truth durante evolução

A v2 precisava avançar sem reescrever todo o legado. A decisão foi usar SQLite como writer único
dos novos domínios e manter JSON/JSONL apenas para compatibilidade, fixture ou export onde ainda há
consumidor. É menos elegante que uma migração instantânea, porém muito mais recuperável.

### Contexto mínimo e structured output

Enviar o banco inteiro ao provider seria simples e inadequado. Context receipts registram
finalidade, quantidade de itens, estimativa de tokens e omissões sensíveis. Outputs passam por
schema e erro tipado. Quota, timeout ou resposta inválida não relaxam regras determinísticas nem a
approval boundary.

### Matching multidomínio

O produto não pode presumir que estrelas no GitHub representam todas as carreiras. Evidências de
pesquisa, docência, certificação, extensão, projeto técnico e resultado profissional entram em um
modelo comum, mas mantêm semânticas próprias. Ausência de item público é lacuna de evidência, não
prova de ausência de competência.

## Decisões e trade-offs

**SQLite em vez de Neo4j ou microservices.** O graph exige relações e consultas rastreáveis, mas o
volume e o modelo local não justificam operação distribuída. SQLite simplifica instalação, backup,
migration e release. O custo é não ter visualização e traversal avançados prontos.

**Determinístico primeiro, IA explicativa.** Regras reproduzíveis calculam Career State e NBA; IA
resume e redige. Isso limita a “criatividade” do sistema, mas torna regressões e decisões auditáveis.

**GitHub como fonte opcional.** Repositórios podem sustentar evidência técnica, porém portfólio é
multidisciplinar. Essa decisão evita transformar ausência de atividade pública em julgamento sobre a
carreira.

**MCP adiado.** O registry interno não foi confundido com uma superfície pública. MCP permanece não
exposto até existirem transporte loopback, token, scopes, ownership e audit equivalentes.

**Sem auto-apply.** Automação de candidatura exigiria browser, sessão, formulários, CAPTCHA e dados
sensíveis com reversibilidade limitada. O produto prepara materiais e registra outcomes, mas a ação
externa continua manual.

## Segurança e confiabilidade

Conteúdo importado é tratado como dado não confiável. Schema estrito rejeita campos extras; tools
desconhecidas ou proibidas não existem no registry; write-local exige proposta e aprovação. Preview,
impacto, expiry, stale, compare-and-set, idempotência, audit e undo formam controles complementares,
não uma única barreira.

Chaves de provider ficam no backend e passam por redaction em diagnósticos. Contexto externo é
opt-in e omite evidências sensíveis por padrão. O processo de release inclui CodeQL, busca por
segredos, auditoria de dependências e SBOM CycloneDX. Esses gates ajudam, mas não substituem leitura
dos findings nem revisão de boundary.

## Qualidade e validação

A estratégia combina testes unitários de regras e contratos, integração de repositories/APIs,
fixtures de migration e recovery, E2E das jornadas web e matriz cross-browser. Ruff e Pyright
cobrem qualidade estática no Python; lint e typecheck cobrem o frontend. MkDocs strict impede que a
documentação publicada acumule links inválidos.

Providers externos são testados apenas por opt-in, com resultados sanitizados e bloqueios de quota
registrados como bloqueios — nunca convertidos em aprovação. Fixtures demo continuam fictícias e
não são apresentadas como validação de carreira real.

## Evolução arquitetural

O projeto evoluiu de módulos conectados para um pipeline de decisão explícito:

```text
Evidence Graph
  → Career State
  → Next Best Actions
  → Copilot Plan
  → Proposed Action
  → Preview e impacto
  → Human Approval
  → execução local
  → Audit e Undo
```

Essa evolução reduziu a dependência de contexto implícito. O frontend também mudou de dashboard de
ferramentas para Career Cockpit, Evidence Inbox, portfólio e fila de aprovação organizados pela
jornada do usuário.

## Resultado atual

Hoje o SotuHire consegue coordenar perfil, evidências profissionais e acadêmicas, portfólio,
currículos, oportunidades, candidaturas, entrevistas, tarefas, planos e outcomes. Ele deriva estado
e prioridades, prepara materiais revisáveis e propõe efeitos locais sem enviar candidatura ou
mensagem automaticamente.

O resultado é uma arquitetura demonstrável: cada recomendação pode apontar para evidências, e cada
escrita do Copilot pode ser revisada, auditada e, quando suportado, desfeita. Isso descreve capacidade
técnica atual — não impacto causal sobre contratação.

## O que aprendi e o que faria diferente

O primeiro aprendizado foi consolidar o source of truth cedo. Compatibilidade gradual é necessária,
mas cada novo domínio deve declarar writer e ownership desde o início; caso contrário, consistência
vira um problema transversal difícil de testar.

Também aprendi que documentação excessivamente fragmentada reduz a compreensão mesmo quando cada
arquivo está correto. Conceitos coesos como Career State, NBA, Tool Registry e Approval Queue ficaram
mais úteis em um documento central do que em páginas de poucas linhas.

Security gates verdes não dispensam interpretação. Um workflow pode concluir com sucesso e ainda
produzir findings que precisam de classificação humana. Segurança efetiva combina automação,
threat modeling e leitura do contexto.

A separação entre regras determinísticas e IA foi decisiva. Se recomeçasse, formalizaria essa
boundary e os context receipts ainda nas primeiras integrações com providers. Isso reduz retrabalho
e torna custo, privacidade e fallback observáveis.

Por fim, eu priorizaria mais cedo evidência e feedback de uso em vez de quantidade de features. Uma
capacidade pequena, rastreável e testada ensina mais sobre o produto que várias telas sem consumidor
ou source of truth claro.

## Limitações e próximos passos

A visualização avançada do graph e o merge visual continuam API-first. Portfólio ainda não possui
export HTML/PDF dedicado. A timeline histórica não tem explorer completo, e telas históricas ainda
passam por migração incremental de i18n. MCP permanece fora da v2.0.

Próximos investimentos dependem de feedback real: qualidade de recomendações com amostra declarada,
acessibilidade, conectores aprovados e redução gradual dos stores legados. O
[roadmap pós-v2](../01-product/roadmap.md) preserva esses limites sem prometer automação crítica.
