# Plano de avaliação de IA

## Objetivo

Criar um benchmark local, reproduzível e multiárea para os fluxos de currículo, vaga, Match, ATS, Tailor, Lattes, Editais, Radar e GitHub. Esta etapa prepara contratos e fixtures; resultados comparativos completos serão publicados somente depois de execução controlada.

## Unidade de avaliação

Cada caso deve conter:

```json
{
  "case_id": "",
  "domain": "",
  "feature": "",
  "input_fixture": "",
  "allowed_context_refs": [],
  "expected_schema": "",
  "gold_facts": [],
  "gold_evidence": [],
  "forbidden_claims": [],
  "dedupe_group": "",
  "review_notes": ""
}
```

`forbidden_claims` descreve fatos que o sistema não pode inferir, como registro profissional ativo, experiência formal, publicação, aprovação, disponibilidade ou requisito atendido sem evidência.

## Cobertura mínima

Áreas: tecnologia/dados, engenharia, saúde, educação, pesquisa, direito, administração/operações, turismo/serviços e artes/design.

Momentos: estudante, pessoa sem experiência formal, estágio, início de carreira, senioridade intermediária, transição e retorno ao mercado.

Documentos: currículo curto/longo, vaga estruturada/informal, Lattes, README, repositório, edital, captura com JSON-LD e entrada incompleta.

## Métricas e cálculo

### Extração

- `schema_validity = respostas válidas / respostas executadas`;
- `field_accuracy = campos corretos / campos anotados`;
- medir datas, valores, listas e entidades separadamente;
- campo ausente não equivale a campo incorreto quando a evidência não existe.

### Evidência

- `evidence_precision = evidências que sustentam claim / evidências citadas`;
- `evidence_recall = evidências relevantes recuperadas / evidências relevantes anotadas`;
- `unsupported_claim_rate = claims sem suporte / claims verificáveis`;
- `hallucination_rate = claims inventados ou contraditórios / claims verificáveis`.

### Confiança

Agrupar previsões em faixas de confiança e comparar confiança média com acurácia observada. A avaliação deve publicar erro de calibração e amostras por faixa; não basta uma média global.

### Operação

- fallback por feature/provider/modelo;
- latência mediana, p90 e p95;
- tokens de entrada/saída quando o provider disponibilizar;
- custo estimado, nunca valor de cobrança tratado como exato;
- taxa de schema inválido e retry.

### Revisão humana

Para cada sugestão: aceitar, aceitar com edição, rejeitar, insuficiente ou não aplicável. Registrar o motivo em taxonomia curta: evidência errada, omissão, tom, granularidade, duplicata, risco, privacidade ou outro.

### Deduplicação

Avaliar pares e grupos:

- mesma vaga com tracking diferente;
- mesma vaga capturada manualmente e pela extensão;
- mesma vaga em portais distintos;
- empresas diferentes com descrições parecidas;
- edital com URLs distintas e mesmo número/órgão/banca;
- publicações por DOI, ORCID, Lattes e repositórios owner/repo;
- snapshots idênticos e versões alteradas.

## Protocolo por provider

1. executar o caminho local e salvar trace seguro;
2. executar mocks estruturados no CI;
3. opcionalmente executar provider externo com chave temporária local;
4. validar schema antes de calcular conteúdo;
5. comparar somente casos com mesma versão de prompt/dataset;
6. separar falha de rede, fallback e falha de conteúdo;
7. nunca incluir chave ou documento pessoal em output.

## Critério de regressão

O baseline inicial será medido antes de definir threshold bloqueante. Depois disso, uma mudança não deve reduzir schema validity, evidence precision/recall ou aumentar unsupported claim/hallucination sem análise explícita. Custo e latência são trade-offs, não substitutos de segurança.

## Entregas futuras

- runner de benchmark por feature/provider;
- anotador/revisor local;
- relatório agregado JSON/Markdown;
- comparação entre commits e prompts;
- dashboard de aceitação e outcomes;
- baseline publicado sem dados pessoais.

Até essas entregas existirem, nenhuma documentação deve afirmar que um provider “vence” outro ou que existe taxa de alucinação medida.
