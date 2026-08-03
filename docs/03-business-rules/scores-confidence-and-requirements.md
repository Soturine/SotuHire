# Requisitos, scores, confiança e risco

## Estados de requisito

O estado canônico de um requisito é `met`, `partial`, `missing`, `unknown` ou
`not_applicable`.

- `unknown` significa informação insuficiente. Ele reduz confiança, não o fit conhecido.
- `not_applicable` significa que o requisito/dimensão não pertence ao contexto profissional e é
  excluído do denominador.
- `missing` só é usado quando o requisito foi entendido e a evidência analisável realmente não o
  sustenta.
- licenças e registros profissionais obrigatórios conhecidos continuam bloqueadores explícitos;
  ausência confirmada pode limitar recomendação e score, enquanto licença não especificada fica
  `unknown` até revisão.

## Métricas independentes

As métricas não são aliases entre si:

| Métrica | Pergunta respondida |
| --- | --- |
| Match | requisitos profissionais conhecidos atendidos pela evidência |
| ATS | alinhamento textual/estrutural do currículo com a vaga |
| Readiness | preparação do material e das informações para candidatar |
| Opportunity fit | preferências, local, contrato e objetivo da pessoa |
| Evidence coverage | proporção de evidências revisadas/confirmadas |
| Requirement coverage | proporção `met`/`partial` entre requisitos aplicáveis e conhecidos |
| Confidence | suficiência e qualidade do material usado para calcular |
| Risk | gaps obrigatórios, claims sem suporte e condições de bloqueio |

Não se salva coverage com o nome de Match ou ATS. Quando nenhum requisito é conhecido,
`assessed_match_score` e `requirement_coverage` são `null` e o status é `insufficient`; o campo
numérico legado permanece apenas para compatibilidade até a retirada versionada. Readiness
expõe valores canônicos anuláveis em paralelo aos campos legados persistidos.

## Fórmulas e denominadores

Requirement coverage usa `met=1`, `partial=0,5`, `missing=0`; `unknown` e
`not_applicable` não entram no denominador. Inserir um requisito `unknown` não pode alterar o fit
calculado sobre fatos conhecidos, mas reduz a confiança. Dimensões `not_applicable`, como GitHub
fora de áreas relevantes, são removidas também do peso total de readiness.

Evidence coverage conta confirmação humana, nunca a simples presença de `source_ref`. Scores
determinísticos continuam produzidos por código; IA pode explicar ou sugerir revisão, mas não
reescreve score, status, denominador, confidence ou risk.
