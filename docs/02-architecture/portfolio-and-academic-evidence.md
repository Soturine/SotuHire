# Portfólio e evidência acadêmica/profissional

O portfólio da v2.0 representa trabalho demonstrável sem assumir que toda carreira é software ou
que todo projeto está no GitHub. Ele conecta produção profissional, acadêmica, técnica, artística e
voluntária ao mesmo modelo de evidências revisáveis.

## Por que é um domínio próprio

O Perfil Universal descreve a pessoa; o portfólio apresenta trabalhos selecionados. Um item pode
combinar várias evidências e destacar contribuição, ferramentas e resultados sem copiar toda a
trajetória para uma página pública.

GitHub é uma fonte possível para software, não um requisito. Pesquisa, aula, projeto de engenharia,
case de design, artigo, apresentação, vídeo, arte ou protótipo de hardware têm o mesmo direito de
ser representados.

## Modelo de item

`portfolio_items` registra:

- título, tipo e descrição;
- papel e contribuição da pessoa;
- links validados;
- skills e ferramentas;
- `evidence_refs` e `source_refs`;
- visibilidade;
- estado de revisão e confiança;
- timestamps locais.

Os tipos incluem software, engenharia, design, pesquisa, publicação, ensino, case study,
apresentação, vídeo, áudio, escrita, arte visual, arquitetura, dados, eletrônica, hardware,
acadêmico, voluntariado e custom.

## Evidência acadêmica

Pesquisa, TCC, iniciação científica, publicação, evento, monitoria, docência, extensão e curso usam
nós tipados no Evidence Graph. Importação de Lattes ou documento produz candidatos: o usuário
confirma autoria, período, instituição e relação com skills antes de usar o item.

Publicação e participação em evento não devem ser confundidas. Da mesma forma, conclusão de curso,
formação formal e certificação mantêm tipos diferentes porque sustentam claims diferentes.

## Evidência profissional

Experiência, projeto, processo, treinamento, certificação, voluntariado e outcome podem sustentar um
item de portfólio. A descrição deve separar responsabilidade, contribuição e resultado.

Resultado numérico só entra quando confirmado por fonte ou pelo usuário. O sistema não completa
percentuais, receita, alcance ou ganho de performance por plausibilidade.

## Registros profissionais

Registros profissionais têm campos sensíveis e podem depender de jurisdição, categoria e validade.
Eles demonstram habilitação declarada, mas o SotuHire não substitui consulta ao órgão oficial.

O número do registro fica fora de contexto externo por padrão. Um portfólio pode mencionar a
existência de habilitação quando apropriado sem expor o identificador completo.

## Links e anexos

Links são URLs validadas e continuam sendo conteúdo externo não confiável. Anexos são referenciados
por metadata e hash nos fluxos compatíveis; não são executados e não concedem permissão ao Copilot.

Antes de tornar um item visível, revise dados pessoais, nomes de clientes, material confidencial e
direitos de publicação.

## Integração com o Evidence Graph

Um item de portfólio pode apontar para projetos, publicações, experiências e skills. A edge
`portfolio_item_evidences_project`, por exemplo, preserva a distinção entre a apresentação do
trabalho e o projeto que ela representa.

Relações candidatas permanecem revisáveis. Criar o item não confirma automaticamente todas as
skills listadas.

## Integração com Career State e Match

Career State usa itens confirmados para medir cobertura de projetos e identificar lacunas de
portfólio. Match pode usar evidências associadas para comparar requisitos, mas ausência de item
público não prova ausência de competência.

Next Best Actions pode recomendar revisar ou completar um item. Essa recomendação continua
determinística; IA pode ajudar a redigir a descrição, nunca inventar a evidência.

## Privacidade e publicação

Visibilidade é uma decisão do usuário. A v2.0 não publica automaticamente, não envia para rede
social e não gera site público sem ação explícita. Export HTML/PDF dedicado permanece pós-v2.

## Source of truth e limites

SQLite schema 8 é o writer dos itens v2. GitHub, Lattes e documentos são fontes, não stores
autoritativos do portfólio. O domínio não valida diploma, autoria externa, licença profissional ou
direito autoral.

## Exemplo

```text
Item: Projeto de extensão — oficina de dados
Tipo: teaching
Papel: planejamento e facilitação
Evidências: atividade de extensão confirmada + material da oficina
Skills: comunicação (confirmed), visualização de dados (candidate)
Visibilidade: private
```

O item pode ser útil no Career State mesmo privado; a skill candidata não vira claim confirmado.

## Links relacionados

- [Evidence Graph](evidence-graph.md)
- [Guia da jornada e portfólio](../05-user-guide/career-workflow.md#portfolio)
- [GitHub como fonte de portfólio](../05-data-sources/github-portfolio-analyzer.md)
- [Privacidade do contexto](../04-ai/copilot-context-and-privacy.md)
