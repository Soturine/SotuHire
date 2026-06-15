# Regras de negócio multiárea

## Objetivo

Este documento define regras para o SotuHire funcionar com currículos e vagas de várias áreas, sem ficar preso a desenvolvimento de software, análise de dados ou tecnologia.

A regra principal é:

```text
O SotuHire deve analisar requisitos profissionais, não apenas palavras-chave técnicas.
```

## Princípios

1. Toda vaga deve ser interpretada como um conjunto de requisitos classificados.
2. Toda competência do candidato deve ter evidência ou confidence baixo.
3. Toda sugestão de currículo deve preservar a verdade factual.
4. Registros profissionais e certificações críticas não podem ser inventados.
5. Áreas diferentes precisam de pesos diferentes.
6. Competências transferíveis devem ser valorizadas, mas não confundidas com experiência direta.
7. O usuário deve revisar campos incertos antes de salvar como perfil.

## Tipos de requisito

Cada requisito extraído da vaga deve ter pelo menos:

```json
{
  "text": "COREN ativo",
  "normalized_name": "COREN ativo",
  "category": "professional_license",
  "importance": "required",
  "criticality": "knockout",
  "domain": "nursing",
  "confidence": 0.94
}
```

Categorias recomendadas:

- `education`;
- `degree`;
- `technical_course`;
- `hard_skill`;
- `soft_skill`;
- `tool`;
- `software`;
- `equipment`;
- `methodology`;
- `certification`;
- `professional_license`;
- `regulation`;
- `language`;
- `experience`;
- `environment`;
- `responsibility`;
- `availability`;
- `location`;
- `portfolio`;
- `academic_output`;
- `other`.

## Importância e criticidade

### Importance

- `required`: requisito obrigatório;
- `preferred`: diferencial ou desejável;
- `optional`: citado, mas não decisivo;
- `unclear`: a vaga não deixa claro.

### Criticality

- `low`: pouco impacto;
- `medium`: impacto moderado;
- `high`: impacto forte;
- `knockout`: pode inviabilizar candidatura.

## Regras para profissões regulamentadas

Em áreas regulamentadas, o sistema deve ser conservador.

Exemplos de registros:

- COREN;
- CRP;
- CREA;
- CAU;
- CFT;
- CRM;
- CRF;
- OAB;
- CRC;
- CREF;
- CRO;
- CRBio;
- CRQ.

Regra:

```text
Se a vaga exige registro profissional e o currículo não informa o registro,
o gap deve ser crítico. A recomendação deve ser condicional, nunca inventada.
```

Sugestão permitida:

```text
Se você possui COREN ativo, deixe essa informação visível no topo do currículo.
```

Sugestão proibida:

```text
Adicione COREN ativo ao currículo.
```

## Regras para formação

Formação exigida deve ser tratada como requisito próprio.

Exemplos:

- ensino médio completo;
- curso técnico em enfermagem;
- graduação em Pedagogia;
- graduação em Psicologia;
- Engenharia Civil completa;
- Arquitetura e Urbanismo;
- pós-graduação;
- licenciatura;
- bacharelado.

Regras:

- não assumir curso concluído se o currículo indica "cursando";
- não transformar curso livre em graduação;
- diferenciar curso técnico, graduação, licenciatura e pós;
- se a vaga aceita cursando, não penalizar como conclusão ausente;
- se a vaga exige diploma concluído e o currículo indica cursando, marcar gap.

## Regras para experiência

Experiência deve considerar:

- cargo;
- área;
- contexto;
- responsabilidades;
- ferramentas;
- ambiente de atuação;
- senioridade;
- duração, quando informada.

Não considerar experiência comprovada apenas porque uma palavra aparece em interesses, resumo genérico ou objetivo profissional.

Exemplo:

```text
"Interesse em atuar com cybersecurity" não equivale a experiência em SOC.
```

## Regras para ferramentas e softwares

Ferramentas devem ser normalizadas.

Exemplos:

| Entrada | Normalização |
|---|---|
| JS | JavaScript |
| ReactJS | React |
| Postgres | PostgreSQL |
| Auto CAD | AutoCAD |
| Sketchup | SketchUp |
| Excel avançado | Microsoft Excel |
| Power Point | Microsoft PowerPoint |
| PEP | Prontuário Eletrônico do Paciente |
| SIEM | SIEM |

A normalização deve preservar o termo original como evidência.

## Regras para equipamentos

Algumas áreas usam equipamentos como requisito, não apenas software.

Exemplos:

- equipamentos hospitalares;
- bombas de infusão;
- monitores multiparamétricos;
- osciloscópio;
- CLP;
- instrumentos de medição;
- equipamentos laboratoriais;
- equipamentos de topografia;
- instrumentos odontológicos;
- sistemas de climatização;
- maquinário industrial.

Esses itens devem entrar como `equipment` ou `technical_equipment`, não como keyword genérica.

## Regras para normas e regulamentações

Normas são requisitos importantes em engenharia, saúde, segurança e qualidade.

Exemplos:

- ABNT;
- NR-10;
- NR-12;
- NR-35;
- ISO 27001;
- LGPD;
- ANVISA;
- RDC;
- normas hospitalares;
- normas internas de qualidade;
- boas práticas laboratoriais.

O SotuHire deve diferenciar:

- conhecimento declarado;
- experiência prática;
- certificação formal;
- requisito legal.

## Regras para portfólio

Portfólio muda por área.

| Área | Evidência útil |
|---|---|
| Software | GitHub, deploy, README, testes, arquitetura |
| Cybersecurity | labs, CTFs, writeups, políticas, scripts seguros |
| Arquitetura | Behance, PDF, renders, projeto executivo, pranchas |
| Design de interiores | moodboards, renders, antes/depois, briefing |
| Pedagogia | planos de aula, projetos pedagógicos, relatórios sem dados sensíveis |
| Psicologia | produção acadêmica, cursos, atuação institucional sem dados clínicos |
| Engenharia civil | projetos, planilhas, orçamento, acompanhamento, memorial |
| Saúde | cursos, protocolos, experiências por setor, sem expor pacientes |

## Regras para GitHub

GitHub é evidência forte para software, dados, IA, automação, cybersecurity e algumas engenharias técnicas.

GitHub é evidência secundária ou irrelevante para algumas vagas de saúde, educação, psicologia, arquitetura e áreas operacionais.

Regra:

```text
Não penalizar candidato de área não técnica por não ter GitHub.
```

## Competências transferíveis

O sistema deve detectar competências transferíveis com rótulo próprio.

Exemplo:

```json
{
  "candidate_skill": "planejamento pedagógico",
  "could_help_with": "treinamento corporativo",
  "match_type": "transferable",
  "confidence": 0.76
}
```

Transferível não deve ser igual a match completo.

Categorias transferíveis:

- comunicação;
- didática;
- documentação;
- atendimento;
- análise;
- organização;
- planejamento;
- resolução de problemas;
- gestão de rotina;
- liderança;
- negociação;
- trabalho em equipe;
- pesquisa;
- escrita técnica;
- análise de risco;
- cuidado com pessoas;
- compliance.

## Regras de sugestão segura

Toda sugestão deve cair em uma das classes:

1. **Destacar evidência existente:** algo já aparece no currículo.
2. **Reorganizar texto:** melhorar clareza sem mudar fatos.
3. **Adicionar se verdadeiro:** item aparece na vaga, mas não no currículo.
4. **Desenvolver gap:** item ausente que exige aprendizado real.
5. **Evitar candidatura:** gap crítico não resolvível no curto prazo.

Exemplo seguro:

```text
A vaga pede experiência com UTI. O currículo cita hospital, mas não cita setor.
Se essa experiência existir, especifique o setor. Se não existir, trate como gap real.
```

## Regras de score multiárea

A Match Engine 2.0 deve considerar pelo menos:

- requisitos obrigatórios;
- requisitos desejáveis;
- formação;
- credenciais;
- experiência prática;
- domínio profissional;
- senioridade;
- modalidade/localização;
- ferramentas/equipamentos;
- portfólio/evidências;
- ATS;
- riscos.

Pesos sugeridos por padrão:

```text
required_requirements: 25%
domain_specific_competencies: 20%
education_and_credentials: 15%
experience_evidence: 15%
work_model_location: 10%
tools_equipment_systems: 5%
soft_skills: 5%
risk_adjustment: 5%
```

Os pesos podem mudar por domínio.

Exemplo:

- enfermagem: credencial e setor pesam mais;
- arquitetura: portfólio e ferramentas visuais pesam mais;
- TI: projetos, stack, testes e arquitetura pesam mais;
- pedagogia: etapa de ensino, BNCC e experiência com público pesam mais;
- engenharia civil: obras, orçamento, normas e software pesam mais.

## Critério de qualidade

Uma análise multiárea é aceitável quando:

- não força linguagem de TI em vaga não técnica;
- detecta domínio corretamente;
- separa requisitos por tipo;
- identifica credenciais críticas;
- reconhece competências transferíveis;
- usa confidence;
- explica gaps sem inventar;
- gera recomendações específicas da área.
