# Estratégia multiárea do SotuHire

## Decisão de produto

O SotuHire deve ser tratado como um **copiloto de carreira multiárea**, não como uma ferramenta focada apenas em tecnologia, desenvolvimento, análise de dados ou vagas de TI.

A versão v0.9.0 já tem memória, RAG local, tracker, análise assistida por extensão, análise de GitHub/portfólio e extração opcional por IA. A próxima evolução precisa impedir que o produto fique enviesado pelos exemplos iniciais de Dev, Analista, IA, automação ou cybersecurity.

A visão correta passa a ser:

```text
SotuHire é um copiloto local-first de carreira que interpreta currículos, vagas,
portfólios e evidências profissionais de múltiplas áreas, gerando análise explicável,
ATS, matching e recomendações com revisão humana.
```

## Áreas que devem funcionar

O sistema deve aceitar currículos e vagas de áreas como:

- desenvolvimento de software;
- dados, IA, automação e QA;
- cybersecurity, SOC, GRC, infraestrutura e redes;
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
- marketing;
- financeiro;
- recursos humanos;
- cursos técnicos;
- indústria;
- logística;
- saúde;
- educação;
- humanas;
- exatas;
- vagas acadêmicas;
- estágios;
- trainee;
- primeiro emprego;
- jovem aprendiz;
- posições operacionais, técnicas, analíticas e de coordenação.

## O que não fazer

A evolução multiárea não deve virar um sistema com regras hardcoded para cada profissão.

Evitar:

- criar um `if` para cada curso;
- criar um parser completamente separado para cada profissão;
- assumir que toda vaga tem stack técnica;
- assumir que GitHub sempre é evidência central;
- tratar diploma, registro profissional e certificação como simples keyword;
- deixar a IA inventar competências para melhorar match;
- forçar currículos de saúde, humanas ou educação dentro de categorias de TI.

## Estratégia correta

A abordagem recomendada é uma camada de **Domain Intelligence**.

Essa camada deve:

1. detectar o domínio profissional da vaga;
2. detectar o domínio profissional do currículo;
3. classificar requisitos por tipo;
4. normalizar termos, aliases e sinônimos;
5. aplicar regras específicas apenas quando necessário;
6. reconhecer competências transferíveis;
7. gerar explicações baseadas em evidências;
8. deixar campos incertos com confidence baixo;
9. pedir revisão humana quando a inferência for fraca;
10. manter o score final calculável por código.

## Entidade conceitual: CareerDomain

O produto deve passar a reconhecer um domínio profissional como parte do contrato de análise.

Exemplo conceitual:

```json
{
  "primary_domain": "biomedical_engineering",
  "secondary_domains": ["healthcare", "maintenance", "quality"],
  "confidence": 0.84,
  "evidence": [
    "A vaga cita equipamentos hospitalares",
    "A vaga cita manutenção preventiva e corretiva",
    "A vaga cita ANVISA e ambiente hospitalar"
  ]
}
```

A mesma vaga pode pertencer a mais de uma área.

Exemplos:

- engenharia biomédica + saúde + manutenção;
- psicologia + RH + recrutamento;
- pedagogia + inclusão + educação infantil;
- arquitetura + design de interiores + vendas consultivas;
- cybersecurity + compliance + auditoria;
- engenharia civil + orçamento + planejamento;
- técnico em eletrotécnica + manutenção + indústria.

## Classificação de requisitos

O SotuHire deve parar de tratar tudo como uma lista plana de skills.

Cada requisito deve ter tipo, importância, criticidade e evidência.

Tipos recomendados:

- formação;
- diploma;
- curso técnico;
- hard skill;
- soft skill;
- ferramenta;
- software;
- equipamento;
- metodologia;
- certificação;
- registro profissional;
- norma;
- regulamentação;
- idioma;
- experiência prática;
- ambiente de atuação;
- responsabilidade;
- disponibilidade;
- localização;
- portfólio;
- produção acadêmica;
- publicação;
- atendimento ao público;
- documentação;
- liderança;
- gestão.

## Exemplos por área

### Enfermagem

Requisitos comuns:

- COREN ativo;
- técnico ou graduação em enfermagem;
- experiência em UTI;
- centro cirúrgico;
- administração de medicamentos;
- punção venosa;
- prontuário eletrônico;
- escala de plantão;
- atendimento humanizado.

Regra importante:

```text
Se a vaga exigir COREN e o currículo não mostrar COREN, isso deve virar gap crítico.
O sistema não deve sugerir inventar COREN. Deve sugerir: "se possuir, tornar visível".
```

### Psicologia

Requisitos comuns:

- CRP ativo;
- avaliação psicológica;
- atendimento clínico;
- psicologia escolar;
- psicologia organizacional;
- ABA;
- laudos;
- triagem;
- acolhimento;
- atendimento infantil, adulto ou institucional.

Cuidados:

- não expor dados sensíveis de pacientes;
- não inventar abordagem clínica;
- não transformar curso livre em especialização;
- diferenciar estágio, clínica, RH e contexto escolar.

### Pedagogia

Requisitos comuns:

- licenciatura em Pedagogia;
- BNCC;
- alfabetização;
- educação infantil;
- ensino fundamental;
- educação inclusiva;
- planejamento pedagógico;
- mediação;
- relatórios;
- atendimento a alunos com TEA ou DI.

O match deve valorizar experiência real com etapa de ensino e contexto pedagógico, não apenas palavras genéricas como comunicação ou organização.

### Engenharia Civil

Requisitos comuns:

- CREA, quando exigido;
- AutoCAD;
- Revit;
- MS Project;
- orçamento;
- cronograma físico-financeiro;
- acompanhamento de obra;
- medição;
- concreto armado;
- normas ABNT;
- leitura de projetos.

### Arquitetura e Design de Interiores

Requisitos comuns:

- CAU, quando exigido;
- AutoCAD;
- SketchUp;
- Revit;
- Promob;
- renderização;
- projeto executivo;
- detalhamento;
- iluminação;
- ergonomia;
- briefing;
- atendimento ao cliente;
- portfólio visual.

Aqui o sistema deve entender que portfólio pode ser mais importante que GitHub.

### Engenharia Biomédica

Requisitos comuns:

- equipamentos hospitalares;
- calibração;
- manutenção preventiva;
- manutenção corretiva;
- metrologia;
- ANVISA;
- segurança elétrica;
- documentação técnica;
- ambiente hospitalar;
- atendimento a clientes internos.

### Cybersecurity

Requisitos comuns:

- SOC;
- SIEM;
- ISO 27001;
- hardening;
- análise de vulnerabilidades;
- resposta a incidentes;
- GRC;
- threat intelligence;
- logs;
- redes;
- Linux;
- cloud security.

Cuidados:

- não pedir exposição de informações sensíveis;
- não tratar laboratório pessoal como experiência corporativa;
- usar projetos, CTFs e labs como evidência quando estiverem documentados.

## Competências transferíveis

Um diferencial forte do SotuHire deve ser reconhecer habilidades transferíveis.

Exemplos:

| Origem | Possível destino | Competências transferíveis |
|---|---|---|
| Pedagogia | Treinamento corporativo | didática, planejamento, avaliação, comunicação |
| Psicologia | RH | entrevista, escuta, avaliação, comportamento organizacional |
| Enfermagem | Healthtech | rotina hospitalar, prontuário, atendimento, protocolos |
| Técnico em eletrônica | Engenharia biomédica | manutenção, diagnóstico, instrumentos, documentação |
| Engenharia civil | Planejamento | orçamento, cronograma, medição, gestão de fornecedores |
| Arquitetura | Vendas consultivas | briefing, projeto, apresentação, negociação |
| Cybersecurity | Compliance | risco, controles, documentação, auditoria |
| Administração | Operações | processos, indicadores, atendimento, organização |

## Como isso entra no produto

A UI deve permitir que o usuário trabalhe em três modos:

1. **Modo automático:** o SotuHire detecta domínio pelo currículo e pela vaga.
2. **Modo revisável:** o sistema mostra domínio e requisitos detectados para confirmação.
3. **Modo manual:** o usuário corrige área, senioridade, requisitos e preferências.

## Como isso entra nos prompts

Os prompts de extração precisam receber:

- texto bruto do currículo;
- texto bruto da vaga;
- preferências do candidato;
- perfil persistente, quando habilitado;
- evidências de GitHub/portfólio, quando relevantes;
- domínio detectado anteriormente;
- idioma esperado da resposta;
- modo de análise.

Os prompts devem retornar:

- domínio primário;
- domínios secundários;
- requisitos classificados;
- credenciais críticas;
- campos ausentes;
- confidence por campo;
- evidências;
- sugestões seguras.

## Como isso entra nos testes

Criar fixtures multiárea:

```text
tests/fixtures/resumes/resume_enfermagem.txt
tests/fixtures/resumes/resume_pedagogia.txt
tests/fixtures/resumes/resume_psicologia.txt
tests/fixtures/resumes/resume_civil.txt
tests/fixtures/resumes/resume_biomedica.txt
tests/fixtures/resumes/resume_arquitetura.txt
tests/fixtures/resumes/resume_cybersecurity.txt
tests/fixtures/jobs/job_enfermeiro_uti.txt
tests/fixtures/jobs/job_professor_fundamental.txt
tests/fixtures/jobs/job_psicologo_rh.txt
tests/fixtures/jobs/job_engenheiro_civil_obras.txt
tests/fixtures/jobs/job_engenheiro_biomedico.txt
tests/fixtures/jobs/job_arquiteto_interiores.txt
tests/fixtures/jobs/job_analista_soc.txt
```

Testes esperados:

- detectar domínio da vaga;
- detectar domínio do currículo;
- classificar requisito obrigatório;
- separar obrigatório de desejável;
- reconhecer registro profissional crítico;
- não inventar registro ausente;
- identificar competências transferíveis;
- gerar score coerente;
- gerar explicação por evidência;
- pedir revisão quando confidence for baixo.

## Impacto no roadmap

Essa estratégia deve entrar como base das versões:

- **v0.10:** extração estruturada por IA e Domain Intelligence inicial;
- **v0.11:** GitHub/Portfolio Analyzer 2.0 e evidências por arquivo;
- **v0.12:** Match Engine 2.0 multiárea;
- **v1.0:** versão generalista estável, demonstrável e confiável.

## Critério de pronto

A estratégia multiárea estará pronta quando o SotuHire conseguir analisar, com exemplos fictícios, pelo menos:

- uma vaga de TI;
- uma vaga de enfermagem;
- uma vaga de pedagogia;
- uma vaga de engenharia civil;
- uma vaga de psicologia ou RH;
- uma vaga de arquitetura/design;
- uma vaga técnica ou industrial.

Cada análise deve mostrar:

- domínio detectado;
- requisitos classificados;
- gaps críticos;
- competências transferíveis;
- score explicável;
- recomendações sem invenção.
