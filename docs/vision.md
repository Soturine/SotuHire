# Visão do Produto

## Visão atual

O SotuHire é um copiloto de carreira local-first, multiárea e explicável para transformar dados profissionais em decisões melhores de candidatura.

Ele deve ajudar uma pessoa a entender:

- o que o currículo realmente comunica;
- o que uma vaga realmente exige;
- quais evidências profissionais existem no currículo, GitHub, portfólio, histórico e memória local;
- onde há aderência, lacunas, riscos e oportunidades;
- como adaptar o currículo sem inventar experiência, formação, certificação ou credencial;
- quais vagas fazem sentido para o perfil atual;
- quais projetos, experiências ou estudos podem fortalecer o próximo passo profissional.

A visão atual não é criar um robô de candidatura automática. O SotuHire é um sistema de inteligência de carreira com humano no controle.

## Posicionamento

O SotuHire deve ser descrito como:

> Um copiloto local-first de inteligência de carreira que analisa currículos, vagas, portfólios e evidências profissionais para gerar matching explicável, sugestões ATS seguras e um plano de evolução para múltiplas áreas profissionais.

Ele não deve ser descrito como:

- bot de LinkedIn;
- bot de spam de currículo;
- ferramenta de candidatura automática;
- crawler agressivo;
- sistema que promete aprovação;
- gerador de currículo com informações inventadas.

## Público-alvo atual

O projeto começou com foco natural em tecnologia, estágios, desenvolvimento, dados, IA, QA e automação, mas a visão atual é multiárea.

O SotuHire deve funcionar para perfis como:

- desenvolvimento de software;
- dados e inteligência artificial;
- QA e automação;
- cybersecurity;
- engenharia biomédica;
- engenharia civil;
- engenharia elétrica;
- engenharia mecânica;
- engenharia de produção;
- arquitetura;
- design de interiores;
- enfermagem;
- psicologia;
- pedagogia;
- administração;
- financeiro;
- marketing;
- logística;
- indústria;
- cursos técnicos;
- humanas;
- exatas;
- saúde;
- educação;
- estágio;
- jovem aprendiz;
- transição de carreira.

O produto deve aceitar que uma vaga pode pertencer a mais de um domínio. Exemplo: uma vaga de engenharia biomédica pode misturar saúde, manutenção, equipamentos, normas, documentação, atendimento e qualidade.

## Problema que o produto resolve

Candidatos normalmente enfrentam cinco problemas:

1. O currículo não comunica claramente as evidências reais da pessoa.
2. Vagas misturam requisitos obrigatórios, desejáveis, responsabilidades e texto promocional.
3. Ferramentas de ATS e matching costumam ser caixas-pretas ou focadas em palavras-chave simples.
4. Portfólios, GitHub e projetos pessoais raramente são conectados ao currículo e às vagas.
5. Candidatos recebem dicas genéricas que às vezes incentivam exageros ou invenção de competências.

O SotuHire deve resolver isso com análise estruturada, evidências, confiança por campo, sugestões seguras e rastreabilidade.

## Proposta de valor

O SotuHire entrega valor quando consegue responder de forma clara:

- esta vaga combina com este currículo?
- quais requisitos estão comprovados?
- quais requisitos estão ausentes?
- quais requisitos são críticos ou eliminatórios?
- quais competências transferíveis podem ajudar?
- quais palavras-chave ATS fazem sentido destacar?
- quais informações precisam de revisão humana?
- quais projetos do GitHub ou portfólio ajudam nessa candidatura?
- quais melhorias aumentam a força do currículo sem inventar nada?

## Princípios do produto

### 1. Local-first

Dados sensíveis de currículo, histórico, preferências e candidaturas devem ficar localmente por padrão.

IA externa pode ser usada, mas deve ser opcional, configurável e limitada ao contexto necessário.

### 2. Humano no controle

O sistema sugere, explica, estrutura e organiza. O usuário decide.

O SotuHire não deve aplicar automaticamente em vagas nem tomar ações irreversíveis sem revisão.

### 3. Explicabilidade

Todo score precisa ter motivo.

Um bom resultado não é apenas:

```txt
Match: 82%
```

Um bom resultado explica:

```txt
Match forte em Java, SQL e Git.
Gap parcial em Docker.
Senioridade compatível com Jr/Pleno.
Vaga remota compatível.
Registro profissional não se aplica.
Confiança geral: 0.84.
```

### 4. Evidência antes de afirmação

O sistema deve diferenciar:

- algo encontrado no currículo;
- algo inferido com confiança;
- algo presente no GitHub;
- algo presente no portfólio;
- algo citado pela memória local;
- algo não evidenciado.

Nenhuma recomendação deve transformar uma inferência fraca em afirmação forte.

### 5. Não inventar experiência

O SotuHire pode sugerir:

```txt
Se você realmente possui experiência com AutoCAD, deixe isso mais visível na seção de habilidades.
```

Mas não deve sugerir:

```txt
Adicione AutoCAD ao currículo.
```

O mesmo vale para COREN, CRP, CREA, CAU, CFT, OAB, certificações, idiomas, resultados, anos de experiência e cargos.

### 6. Multiárea sem hardcode excessivo

O produto não deve virar uma lista de `if profissão == X`.

A abordagem correta é usar:

- classificação de domínio;
- taxonomia de requisitos;
- catálogos configuráveis;
- normalização de termos;
- regras específicas somente quando necessário;
- fallback generalista.

### 7. IA como interpretadora, código como controle

IA pode extrair, classificar, explicar e sugerir.

Código deve validar, calcular, aplicar pesos, bloquear inconsistências e salvar histórico.

## Escopo atual da v0.9.0

A v0.9.0 representa uma base ampla de produto, com:

- análise local de currículo e vaga;
- Match Score;
- ATS Score;
- Opportunity Fit Score;
- Risk Score;
- Resume Tailor;
- Career Memory;
- RAG lexical local;
- perfil profissional persistente;
- tracker de candidaturas;
- dashboard;
- Search Intelligence;
- Hidden Jobs Radar;
- extensão assistiva;
- Local Companion API;
- análise inicial de GitHub e portfólio;
- Gemini opcional.

A v0.9.0 não deve ser tratada como MVP inicial. O próximo ciclo deve estabilizar e aprofundar a inteligência.

## Direção técnica

A direção técnica pós-v0.9.0 é:

```txt
v0.9.1  -> documentação coerente e prompts separados
v0.10.0 -> extração estruturada com IA e Domain Intelligence
v0.11.0 -> GitHub Analyzer 2.0 baseado em evidências
v0.12.0 -> Match Engine 2.0 multiárea
v1.0    -> plataforma generalista estável e demonstrável
```

## Decisões importantes

### Site e extensão

A extensão deve ser uma ponte leve entre navegador e SotuHire local.

A análise pesada deve ficar no site/backend local, onde pode ser reaproveitada pelo currículo, tracker, memória, portfólio e matching.

### Prompts

Prompts devem ser separados por função, versionados e validados por schema.

Um prompt gigante único para tudo aumenta risco de confusão, custo, alucinação e manutenção difícil.

### GitHub e portfólio

A análise de GitHub deve evoluir de sinais visíveis da página para uma análise baseada em:

- GitHub API;
- árvore completa do repositório;
- arquivos prioritários;
- sampler inteligente;
- grafo de dependências;
- prompt estruturado;
- evidências por arquivo;
- valor para currículo e vagas.

### Currículo e vaga

A extração de currículo e vaga deve deixar de depender apenas de heurísticas.

O caminho correto é:

```txt
parser local
+ IA estruturada
+ validação Pydantic
+ confidence por campo
+ comparação IA x heurística
+ revisão humana
```

## Fora de escopo conceitual

O SotuHire não deve prometer:

- aprovação garantida;
- ranqueamento perfeito;
- substituição de recrutador;
- criação de experiência falsa;
- automação de candidatura em massa;
- envio automático de mensagens para recrutadores;
- manipulação de plataformas.

## Métrica de sucesso

O projeto é bem-sucedido quando consegue gerar, de forma confiável:

- perfil profissional estruturado;
- vaga estruturada;
- match explicável;
- gaps críticos;
- sugestões ATS seguras;
- evidências do portfólio;
- plano de melhoria;
- histórico de candidaturas;
- documentação clara para manutenção e evolução.
