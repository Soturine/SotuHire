# Visão do Produto

## Declaração de visão

O SotuHire é um copiloto local-first de inteligência de carreira para analisar currículos, vagas, portfólios, GitHub, histórico profissional e evidências de competência em múltiplas áreas.

O objetivo é ajudar o usuário a tomar decisões melhores sobre candidatura, adaptação de currículo, evolução profissional e priorização de oportunidades.

O SotuHire não deve ser visto como um bot de candidatura. Ele deve ser visto como um sistema de análise, explicação, organização e recomendação com humano no controle.

## Posicionamento em uma frase

> SotuHire transforma currículo, vaga e evidências profissionais em matching explicável, sugestões ATS seguras e plano de evolução para múltiplas áreas de carreira.

## O que o produto é

O SotuHire é:

- local-first;
- explicável;
- multiárea;
- orientado a evidências;
- apoiado por IA opcional;
- voltado para decisão humana;
- útil para currículo, vaga, tracker, portfólio e GitHub;
- desenhado para não inventar credenciais ou experiências.

## O que o produto não é

O SotuHire não é:

- robô de candidatura automática;
- gerador de currículo falso;
- ferramenta para inflar experiência;
- sistema que promete contratação;
- ATS mágico sem explicação;
- crawler agressivo;
- substituto de julgamento humano;
- ferramenta exclusiva para devs.

## Usuários-alvo

O usuário-alvo é qualquer pessoa que precisa conectar currículo, vaga, histórico e evidências profissionais de forma mais clara.

Exemplos:

- estudantes buscando estágio;
- pessoas em transição de carreira;
- profissionais de tecnologia;
- profissionais de saúde;
- profissionais de educação;
- engenharias;
- arquitetura e design;
- cursos técnicos;
- administração e negócios;
- pessoas buscando primeiro emprego;
- profissionais que querem adaptar currículo com segurança;
- candidatos que possuem portfólio, GitHub ou projetos pessoais;
- candidatos que precisam entender por que uma vaga combina ou não combina.

## Áreas que o produto deve suportar

O produto deve ser projetado para múltiplas áreas desde o motor interno, não apenas pela interface.

Áreas esperadas:

- desenvolvimento de software;
- dados e IA;
- QA e automação;
- cybersecurity;
- engenharia biomédica;
- engenharia civil;
- engenharia elétrica;
- engenharia mecânica;
- engenharia de produção;
- enfermagem;
- psicologia;
- pedagogia;
- arquitetura;
- design de interiores;
- administração;
- financeiro;
- marketing;
- logística;
- indústria;
- cursos técnicos;
- saúde;
- educação;
- humanas;
- exatas.

Uma vaga pode pertencer a mais de um domínio. O sistema deve aceitar domínios primários e secundários.

## Problema central

Candidatos costumam ter dificuldade em responder perguntas simples:

- Meu currículo comunica bem o que eu sei fazer?
- A vaga realmente combina comigo?
- Quais requisitos são obrigatórios e quais são desejáveis?
- O que eu já tenho evidência para afirmar?
- O que eu não deveria afirmar?
- Como adaptar o currículo sem mentir?
- Meu GitHub ou portfólio ajuda nessa vaga?
- O que devo melhorar primeiro?
- Qual vaga vale mais meu tempo?

O SotuHire deve transformar essas perguntas em análises estruturadas.

## Proposta de valor

O produto entrega valor quando gera respostas como:

- match explicado por requisito;
- ATS score com motivo;
- gaps críticos separados de gaps leves;
- sugestões seguras de currículo;
- evidências por fonte;
- competências transferíveis;
- alerta de campos incertos;
- priorização de oportunidades;
- plano de melhoria prático.

## Princípios fundamentais

### 1. Local-first

Dados de currículo, histórico, preferências e candidaturas devem ficar localmente por padrão.

IA externa pode ser usada, mas deve ser opcional, configurável e limitada ao contexto necessário.

### 2. Humano no controle

O sistema deve sugerir, explicar e organizar. O usuário decide.

### 3. Sem invenção

O SotuHire nunca deve inventar:

- experiência profissional;
- cargo;
- tempo de experiência;
- formação;
- certificação;
- registro profissional;
- idioma;
- resultado mensurável;
- empresa;
- aprovação;
- participação em projeto.

Quando algo for possível, mas não comprovado, o sistema deve dizer:

```txt
Se isso for verdadeiro, deixe mais visível no currículo.
```

E não:

```txt
Adicione isso ao currículo.
```

### 4. Explicabilidade

Todo score deve ter explicação.

Um score sem justificativa é fraco. O SotuHire deve sempre responder:

- o que bateu;
- o que faltou;
- o que é crítico;
- o que é parcial;
- qual evidência sustenta a análise;
- qual confiança o sistema tem na resposta.

### 5. Multiárea real

Multiárea não significa trocar palavras de TI por palavras de outras áreas.

Multiárea significa entender tipos de requisito:

- formação;
- registro profissional;
- certificação;
- experiência prática;
- ferramenta;
- software;
- equipamento;
- norma;
- metodologia;
- ambiente de atuação;
- público atendido;
- responsabilidade;
- soft skill;
- portfólio;
- disponibilidade.

### 6. IA com contrato

A IA deve operar por prompts versionados, schemas de entrada e saída, confidence rules e validação.

O código deve validar a resposta e calcular scores finais.

## Modelo mental do produto

O SotuHire deve funcionar como um funil de inteligência:

```txt
Currículo bruto
+ Vaga bruta
+ Preferências
+ Histórico
+ GitHub/portfólio
        ↓
Extração estruturada
        ↓
Classificação de domínio
        ↓
Normalização de requisitos
        ↓
Matching por evidências
        ↓
ATS e tailoring seguro
        ↓
Tracker, memória e plano de melhoria
```

## Núcleos do produto

### Currículo

O currículo é a fonte principal de evidência formal.

O sistema deve extrair:

- identidade básica;
- resumo;
- formação;
- experiências;
- projetos;
- skills;
- idiomas;
- certificações;
- registros profissionais;
- domínios;
- lacunas;
- risco ATS;
- confidence por campo.

### Vaga

A vaga deve ser interpretada como estrutura, não como texto plano.

O sistema deve separar:

- requisitos obrigatórios;
- requisitos desejáveis;
- responsabilidades;
- benefícios;
- senioridade;
- domínio;
- localidade;
- modalidade;
- tipo de contrato;
- red flags;
- requisitos eliminatórios.

### Matching

Matching deve ser comparação explicável entre requisitos e evidências.

O score final deve considerar:

- requisito obrigatório;
- requisito desejável;
- formação;
- credenciais;
- experiência;
- domínio;
- senioridade;
- evidências;
- ATS;
- risco;
- preferências.

### ATS

ATS não deve ser só lista de keywords.

ATS deve considerar:

- clareza;
- estrutura;
- seções ausentes;
- vocabulário da vaga;
- evidência real;
- formatação;
- redundância;
- aderência ao domínio.

### GitHub e portfólio

GitHub e portfólio devem ser tratados como evidência profissional.

Eles podem demonstrar:

- tecnologia;
- arquitetura;
- documentação;
- testes;
- manutenção;
- profundidade técnica;
- consistência;
- evolução;
- capacidade de explicar projeto;
- valor para vaga.

### Tracker e memória

Tracker e memória devem registrar aprendizado e histórico de decisões.

Eles ajudam a responder:

- quais vagas foram analisadas;
- quais tinham maior aderência;
- quais gaps aparecem com frequência;
- quais currículos foram adaptados;
- quais projetos ajudam mais;
- quais áreas fazem mais sentido para o perfil.

## Diferenciais do SotuHire

- Local-first.
- IA opcional.
- Multiárea.
- Explicação por evidência.
- Integração entre currículo, vaga, GitHub, portfólio e tracker.
- Foco em sugestão segura, não invenção.
- Possibilidade de funcionar como projeto de portfólio forte e como ferramenta real.

## Critério de sucesso

O SotuHire está funcionando bem quando o usuário consegue:

1. Inserir currículo.
2. Inserir ou capturar vaga.
3. Entender requisitos da vaga.
4. Ver aderência com explicação.
5. Ver gaps reais.
6. Ver sugestões ATS seguras.
7. Usar GitHub/portfólio como evidência.
8. Decidir se vale aplicar.
9. Salvar a análise no tracker.
10. Saber o que melhorar para próximas vagas.

## Estado v1.0.0

Na v1.0.0, o SotuHire já é uma versão estável e demonstrável:

- o app completo roda localmente via Streamlit;
- GitHub Pages funciona como site estático de produto, documentação e demo;
- Match Engine 2.0 aparece no fluxo principal com confidence, evidências e gaps críticos;
- ATS e Resume Tailor usam sinais do match para preservar sugestões seguras;
- exemplos fictícios multiárea mostram backend, enfermagem, pedagogia, engenharia civil,
  arquitetura e cybersecurity.

## Visão de longo prazo

A versão madura do SotuHire deve ser uma plataforma local-first de inteligência de carreira que ajuda pessoas de diferentes áreas a transformar experiências, projetos e habilidades em decisões profissionais melhores.

O produto deve ser forte o suficiente para um dev mostrar como portfólio, mas genérico o suficiente para analisar currículo e vaga de enfermagem, pedagogia, psicologia, engenharia, arquitetura, design, cursos técnicos e áreas administrativas.
