# Estratégia de prompts

## Objetivo

A IA deve interpretar linguagem natural, comparar currículo e vaga, explicar compatibilidade e sugerir melhorias. Ela não deve tomar decisões invisíveis nem inventar informações.

## Papel do modelo

O prompt deve posicionar o modelo como:

> Especialista em recrutamento técnico, ATS, análise de currículo e vagas de tecnologia, com foco em candidatos de estágio/júnior.

## Regras do prompt

O modelo deve:

- responder em português;
- não inventar experiências;
- diferenciar requisito obrigatório de desejável;
- explicar o score;
- sugerir palavras-chave apenas quando fizer sentido;
- deixar claro quando algo não aparece no currículo;
- gerar mensagem curta e editável;
- retornar JSON válido quando solicitado.

## Prompt base sugerido

```text
Você é um especialista em recrutamento técnico, ATS e análise de vagas de tecnologia.
Analise o currículo e a descrição da vaga.

Regras:
- Não invente experiências ou habilidades.
- Se uma habilidade não aparecer no currículo, diga que ela está ausente ou precisa ser destacada apenas se for verdadeira.
- Considere senioridade com peso alto.
- Explique os motivos do score.
- Classifique a recomendação como: Aplicar, Aplicar com cautela, Revisar antes de aplicar ou Não aplicar.
- Retorne somente JSON válido no schema solicitado.
```

## Separação de prompts

Evite um prompt gigante no meio do `app.py`. Use funções:

```python
def build_match_prompt(cv_text: str, job_description: str) -> str:
    ...
```

Ou separe:

- system instructions;
- user input;
- schema;
- examples.

## Anti-alucinação

O prompt deve conter instruções claras:

- não assumir graduação concluída se estiver cursando;
- não assumir inglês fluente se não estiver escrito;
- não assumir experiência profissional em IA se só existem projetos pessoais;
- não transformar interesse em habilidade avançada.

## Exemplo de boa resposta

```text
A vaga menciona Power BI. Essa palavra-chave não aparece de forma forte no currículo. Se o candidato realmente tiver experiência, vale destacar em Habilidades ou Projetos.
```

## Exemplo de resposta ruim

```text
O candidato possui Power BI avançado.
```

Se o currículo não diz isso, essa resposta é invenção.

# Atualização: prompts completos, versionados e multiárea

A estratégia anterior de prompt base continua útil como ponto de partida, mas a v0.10+ precisa de prompts completos por função.

O SotuHire não deve usar apenas um prompt genérico de "analise currículo e vaga".

Ele deve usar prompts especializados:

- `resume_extraction_v1`;
- `job_extraction_multi_domain_v1`;
- `match_analysis_evidence_based_v1`;
- `ats_analysis_v1`;
- `resume_tailor_v1`;
- `github_repo_analysis_v2`;
- `hidden_job_detection_v1`.

## Mudança de papel do modelo

O modelo não deve ser posicionado apenas como especialista em recrutamento técnico para estágio/júnior.

Novo papel geral:

```text
Especialista em análise de carreira multiárea, ATS, extração estruturada, requisitos profissionais, portfólio e recomendações seguras, mantendo o usuário no controle.
```

## Contrato mínimo de todo prompt

Todo prompt deve conter:

- `PROMPT_ID`;
- `PROMPT_VERSION`;
- objetivo;
- regras obrigatórias;
- contrato de entrada;
- contrato de saída;
- JSON puro;
- schema Pydantic associado;
- regras de anti-invenção;
- regras de confidence;
- regras de calibração;
- exemplos de campos críticos.

## Entrada rica

Prompts devem receber mais que texto solto.

Exemplo:

```json
{
  "resume_text": "...",
  "job_text": "...",
  "candidate_preferences": {},
  "career_memory_evidence": [],
  "portfolio_evidence": [],
  "analysis_mode": "advanced",
  "language": "pt-BR"
}
```

## Saída rígida

A saída deve ser JSON validável por Pydantic.

Texto livre só deve ser usado como rascunho, nunca como contrato de produto.

Regra:

```text
Sem schema validado, a resposta da IA não entra no tracker, na memória ou no score final.
```

## IA não calcula tudo

A IA deve:

- extrair;
- classificar;
- explicar;
- sugerir;
- listar evidências;
- estimar confidence.

O código deve:

- validar;
- calcular score;
- aplicar pesos;
- travar score por gap crítico;
- registrar histórico;
- comparar versões;
- impedir overclaiming.

## Catálogo completo

Os prompts completos ficam em:

- [Prompt Catalog](prompt-catalog.md)
- [Orquestração de IA e confiança](ai-orchestration-and-confidence.md)

## Critério de qualidade do prompt

Um prompt é bom quando:

- retorna JSON válido na maioria dos casos;
- lida com currículo incompleto;
- lida com vaga informal;
- lida com áreas fora de TI;
- não inventa registro profissional;
- separa obrigatório de desejável;
- aponta confidence baixo quando necessário;
- gera sugestões seguras;
- facilita teste automatizado.
