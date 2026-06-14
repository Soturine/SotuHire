# Career Memory e RAG local

Career Memory é a camada local que registra fatos e eventos úteis da trajetória profissional.
RAG local é o mecanismo que encontra apenas os itens relevantes para a vaga ou consulta atual.

## O que é salvo

- fatos estruturados do currículo, projetos, experiências, formação, skills e links;
- preferências explícitas;
- análises e recomendações anteriores;
- oportunidades, candidaturas e eventos do tracker;
- feedback manual sobre a qualidade das recomendações.

O arquivo padrão é `data/memory/career-memory.jsonl`. O perfil consolidado fica em
`data/memory/career-profile.json`. A pasta `data/` é ignorada pelo Git.

## Recuperação

O retrieval funciona sem IA externa:

1. normaliza e tokeniza a consulta;
2. mede sobreposição de keywords;
3. aplica boost para tags compatíveis;
4. aplica boost por tipo de memória;
5. aplica um boost pequeno por recência;
6. retorna evidências com fonte, trecho e relevância.

## Uso na análise

A análise local incorpora os trechos recuperados aos fatos do currículo, ajustando scores e
recomendação sem inventar informação. A interface mostra as evidências usadas.

Quando Gemini estiver habilitado, o comportamento depende de duas flags:

| Flag | Padrão | Efeito |
| --- | --- | --- |
| Usar memória nesta análise | sim | recupera contexto para a análise local |
| Enviar contexto relevante para Gemini | não | envia apenas o resumo recuperado ao provider |

Desabilitar a primeira flag impede a recuperação. Manter a segunda desabilitada garante que
Gemini não receba memória, mesmo quando a análise local a utiliza.

## Evolução futura

Embeddings locais e reranking podem ser adicionados como opções. Eles não são dependências da
v0.8.0 e não devem substituir evidências rastreáveis.

## Calibração na v0.9.0

O retrieval passa a considerar pesos configuráveis, boost por tipo, penalidade para itens
genéricos ou antigos, limites por tipo e feedback útil/não útil. Cada evidência mostra motivo de
seleção e breakdown de score.

Capturas multiportal usam uma identidade estável. Quando a mesma vaga aparece em LinkedIn e Gupy,
por exemplo, a memória de oportunidade é atualizada em vez de duplicada.

Veja [Calibração de evidências](evidence-calibration.md).
