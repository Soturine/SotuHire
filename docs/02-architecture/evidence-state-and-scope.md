# Estado de evidência e EvidenceScope

## Contrato canônico

Toda evidência revisável usa um dos estados abaixo. O estado é independente da origem, URL,
arquivo ou score de extração.

| Estado | Significado | Pode sustentar afirmação confirmada? |
| --- | --- | --- |
| `candidate` | hipótese extraída ou informada, ainda sem provenance suficiente | não |
| `sourced` | existe uma referência/localização verificável | não |
| `confirmed` | a pessoa revisou e confirmou o conteúdo | sim |
| `rejected` | a pessoa recusou o conteúdo | não; fica fora de análises |
| `stale` | a dependência mudou desde a revisão | não; exige nova revisão |

`source_ref` nunca promove um item a `confirmed`. Compatibilidade com o campo antigo
`confirmed_by_user` é bidirecional, mas o estado de revisão é a representação canônica nova.

Cada `CareerContextEvidence` possui `evidence_id` determinístico, hash de conteúdo, fonte,
referência, localização estruturada opcional (documento, página, seção, entrada, bloco e offsets),
timestamp observado, sensibilidade, confiança e metadados. O ID e o hash não dependem do estado
de revisão, portanto a revisão pode mudar sem apagar a identidade da evidência.

## Escopo imutável

`EvidenceScope` é um snapshot imutável de:

- propósito da análise;
- IDs e referências selecionados;
- opt-in de IA externa;
- opt-in separado para evidência sensível;
- dependency hash dos IDs, hashes, estados e flags de sensibilidade selecionados.

O contexto pode conservar candidatos para revisão, mas adaptadores de domínio recebem somente a
seleção do scope. Itens `rejected` e `stale` são sempre excluídos. Para provider externo, a
interseção é ainda mais restrita: selecionado + `confirmed` + não sensível + opt-in explícito.
Sem opt-in, o formatador externo retorna contexto vazio. Mudar seleção ou revisão cria outro
scope; o anterior não é mutado e continua auditável.

## Persistência e compatibilidade

Perfil e entradas do currículo reconhecem os cinco estados. Registros antigos sem estado são
normalizados como `confirmed` somente quando `confirmed_by_user=true`; uma referência antiga
sem confirmação vira `sourced`. JSON/SQLite legados continuam legíveis, mas não podem elevar
provenance a confirmação.

Outputs devem registrar IDs/hashes de evidência, scope/dependency hash e source location quando
disponível. Exibir uma fonte ajuda a revisar; não autoriza copiar o fato para currículo, kit,
Tracker ou provider.

## Invariantes testados

- `source_ref != confirmed`;
- scope não pode ser alterado depois de criado;
- origem, estado, seleção e sensibilidade são avaliados separadamente;
- replay de uma seleção antiga não contorna `stale`/`rejected`;
- contexto externo sem opt-in é vazio;
- apenas evidência confirmada e selecionada chega a provider externo;
- dependency hash muda quando conteúdo ou estado selecionado muda.
