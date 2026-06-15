# Arquitetura de Prompts

## Objetivo

Este documento define como os prompts do SotuHire devem ser organizados, versionados, validados e conectados ao código.

A partir da v0.10, prompts não devem ser textos soltos espalhados pelo código. Eles devem ser tratados como contratos de produto.

## Princípio central

```txt
IA interpreta, estrutura e explica.
Código valida, calcula, bloqueia e persiste.
```

A IA pode:

- extrair informações;
- classificar requisitos;
- interpretar domínio;
- sugerir melhorias;
- explicar gaps;
- transformar texto em JSON;
- gerar bullets seguros.

O código deve:

- validar schema;
- aplicar regras de negócio;
- calcular score final;
- bloquear inconsistências;
- registrar prompt/model/input/output;
- tratar erro;
- pedir revisão humana quando necessário.

## Por que separar prompts

Um prompt único para tudo tende a:

- ficar grande demais;
- misturar responsabilidades;
- dificultar testes;
- aumentar custo;
- aumentar alucinação;
- tornar versionamento confuso;
- dificultar evolução por função.

Por isso, cada função deve ter um prompt próprio.

## Estrutura de cada prompt

Cada prompt deve ter:

- metadata;
- propósito;
- quando usar;
- quando não usar;
- input contract;
- output schema;
- system prompt;
- user prompt template;
- regras anti-invenção;
- regras de confidence;
- regras de calibração;
- exemplos;
- failure modes;
- retry strategy;
- fixtures de teste;
- módulos relacionados.

## Metadata padrão

```txt
PROMPT_ID: snake_case_name
PROMPT_VERSION: major.minor.patch
STATUS: planned | draft | active | deprecated
OWNER: SotuHire
USED_BY: module/service
OUTPUT_SCHEMA: PydanticModelName
DEFAULT_TEMPERATURE: 0.1
REQUIRES_REVIEW: true | false
```

## Contrato de entrada

O input contract deve descrever exatamente o que o prompt espera receber.

Exemplo:

```json
{
  "resume_text": "string",
  "file_type": "pdf | docx | txt | pasted_text",
  "candidate_preferences": {
    "target_roles": ["string"],
    "target_domains": ["string"],
    "locations": ["string"],
    "work_models": ["remote | hybrid | onsite"],
    "seniority_target": "string | null"
  },
  "existing_profile_memory": "object | null"
}
```

## Contrato de saída

A saída deve ser JSON puro, sem markdown.

Cada campo importante deve ter:

- valor;
- confidence quando fizer sentido;
- evidência quando fizer sentido;
- indicação de revisão quando confidence for baixa.

## Confidence

Confidence deve ser usado para indicar o quanto o modelo está seguro, não para dizer se o candidato é bom ou ruim.

Exemplo:

```json
{
  "field": "seniority",
  "value": "junior",
  "confidence": 0.62,
  "evidence": ["estágio", "projetos acadêmicos"]
}
```

## Anti-invenção

Todos os prompts devem conter regras explícitas contra invenção.

O modelo não deve inventar:

- experiência;
- cargo;
- empresa;
- formação;
- certificação;
- registro profissional;
- idioma;
- resultado;
- tecnologia;
- deploy;
- métrica;
- número de usuários;
- conquista.

## Regras para áreas regulamentadas

Prompts que analisam currículo, vaga, matching ou ATS devem tratar credenciais profissionais como sensíveis.

Exemplos:

- COREN;
- CRP;
- CREA;
- CAU;
- CFT;
- OAB;
- CRC;
- CRF;
- CRM.

O sistema pode dizer:

```txt
Se você possui CRP ativo, deixe essa informação visível.
```

Mas não deve dizer:

```txt
Adicione CRP ao currículo.
```

## Retry strategy

Se a IA retornar JSON inválido:

1. tentar reparar JSON localmente;
2. validar novamente;
3. se falhar, chamar prompt de correção com o erro de schema;
4. se falhar de novo, usar fallback heurístico;
5. marcar análise como `needs_review`.

## Versionamento

Quando mudar schema de saída, aumentar versão major.

Quando mudar critérios ou textos sem quebrar schema, aumentar minor.

Quando corrigir instrução sem mudar comportamento esperado, aumentar patch.

## Logs

Toda análise com IA deve registrar:

- prompt_id;
- prompt_version;
- model;
- provider;
- input_hash;
- output_hash;
- timestamp;
- schema_version;
- validation_status;
- confidence geral.

Não registrar dados sensíveis desnecessários em logs legíveis.

## Relação com testes

Cada prompt deve ter fixtures.

Exemplos mínimos:

- currículo de TI;
- currículo de enfermagem;
- currículo de pedagogia;
- currículo de engenharia civil;
- vaga técnica;
- vaga saúde;
- vaga educação;
- vaga post informal;
- repositório simples;
- repositório com testes;
- repositório sem README.

## Resultado esperado

A arquitetura de prompts deve deixar o projeto pronto para o Codex implementar:

- Prompt Registry;
- Pydantic schemas;
- JSON Guard;
- retry strategy;
- confidence merger;
- AI orchestrator;
- testes multiárea.
