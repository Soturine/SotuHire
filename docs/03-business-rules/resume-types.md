# Tipos de currículo e perfis profissionais

## Objetivo

O SotuHire não deve tratar todo currículo como se fosse o mesmo tipo de documento. Um currículo corporativo otimizado para ATS, um Currículo Lattes, um perfil do LinkedIn, um GitHub e um portfólio têm finalidades diferentes.

Este documento define como o sistema deve lidar com diferentes fontes de perfil profissional sem misturar objetivos.

## Resposta direta

Sim, o SotuHire deve considerar:

- currículo ATS;
- currículo tradicional em PDF/DOCX;
- Currículo Lattes;
- perfil LinkedIn;
- GitHub;
- portfólio;
- histórico acadêmico;
- projetos pessoais;
- certificados;
- experiências técnicas;
- dados estruturados do usuário.

Mas o sistema não deve simplesmente jogar tudo no currículo final. A função do SotuHire é transformar essas fontes em um **perfil estruturado** e depois gerar recomendações adequadas ao tipo de vaga.

## Conceito central: Career Profile

O SotuHire deve criar um perfil central, chamado aqui de `CandidateProfile`.

Esse perfil é uma representação organizada do candidato, independente do formato de origem.

```json
{
  "identity": {
    "name": "Nome do candidato",
    "location": "São José dos Campos, SP",
    "links": ["GitHub", "LinkedIn", "Lattes", "Portfólio"]
  },
  "education": [],
  "experiences": [],
  "projects": [],
  "skills": [],
  "certifications": [],
  "academic_outputs": [],
  "technical_outputs": [],
  "languages": [],
  "career_targets": []
}
```

O parser não deve gerar diretamente um currículo final. Ele deve primeiro preencher esse perfil estruturado.

## Currículo ATS

### O que é

Um currículo ATS é uma versão pensada para ser legível por sistemas de triagem de candidatos.

Características desejáveis:

- texto extraível;
- seções simples;
- títulos claros;
- uma coluna preferencialmente;
- pouca ou nenhuma informação em imagem;
- palavras-chave da vaga;
- experiências e projetos descritos com verbos de ação;
- links escritos por extenso;
- formato limpo.

### Quando usar

Usar para:

- Gupy;
- InfoJobs;
- Indeed;
- Vagas.com;
- Catho;
- sites de carreira;
- ATS corporativos;
- candidaturas em empresas.

### O que o SotuHire deve verificar

- se o texto do PDF é extraível;
- se há seções reconhecíveis;
- se há palavras-chave da vaga;
- se o currículo contém contato e links;
- se há excesso de layout visual;
- se o documento parece mais imagem do que texto;
- se existe compatibilidade com a senioridade da vaga.

## Currículo Lattes

### O que é

O Currículo Lattes é um padrão brasileiro muito usado em contexto acadêmico, científico e de pesquisa. Ele registra formação, produção bibliográfica, produção técnica, eventos, orientações, projetos, bancas, prêmios e outras atividades acadêmicas.

A Plataforma Lattes é mantida pelo CNPq e reúne informações curriculares, grupos de pesquisa e instituições em um sistema voltado à ciência e tecnologia no Brasil.

Referência: [Plataforma Lattes / CNPq](https://lattes.cnpq.br/)

### Por que importa para o SotuHire

Para vagas de tecnologia, dados, IA, pesquisa aplicada, iniciação científica, estágio acadêmico, laboratório, bolsas e empresas com P&D, o Lattes pode conter informações importantes que não aparecem bem em um currículo corporativo comum.

Exemplos úteis:

- iniciação científica;
- projetos acadêmicos;
- publicações;
- apresentações;
- monitorias;
- participação em eventos;
- cursos extracurriculares;
- prêmios;
- orientações;
- produção técnica;
- áreas de pesquisa.

### Risco

O Lattes não deve ser usado como currículo ATS diretamente.

Problemas possíveis:

- é longo demais;
- pode ter linguagem acadêmica demais;
- pode esconder habilidades práticas;
- pode não destacar impacto;
- pode não ser adequado para vaga júnior corporativa;
- pode incluir informações irrelevantes para a vaga.

### Estratégia correta

O SotuHire deve usar o Lattes como fonte de dados, não como currículo final.

Fluxo recomendado:

```text
Currículo Lattes -> extração estruturada -> CandidateProfile -> seleção do que importa -> currículo ATS adaptado
```

Exemplo:

```text
Lattes contém: participação em projeto de pesquisa com Python e análise de dados.
SotuHire transforma em: Projeto acadêmico de análise de dados com Python, destacando coleta, processamento e visualização.
```

## LinkedIn

### Uso no SotuHire

O LinkedIn pode ser usado como fonte assistiva:

- usuário cola o texto do perfil;
- usuário cola descrição de vaga;
- usuário cola texto de post;
- usuário salva link de vaga;
- extensão local pode ler a página aberta pelo usuário, se for transparente e limitada.

### Não usar

Não usar LinkedIn para:

- login automatizado;
- scraping de feed autenticado;
- coleta de perfis em massa;
- download de contatos;
- envio automático de mensagens;
- candidatura automática.

## GitHub

### Uso no SotuHire

O GitHub é importante para vagas técnicas.

O sistema pode analisar, quando o usuário fornecer links:

- README de projetos;
- linguagens usadas;
- tópicos do repositório;
- commits recentes;
- organização do projeto;
- presença de testes;
- CI/CD;
- documentação;
- issues e roadmap.

### Como usar na análise

Para uma vaga de IA, dados ou automação, o SotuHire pode destacar projetos com:

- Python;
- SQL;
- automação;
- LLMs;
- APIs;
- scraping responsável;
- testes;
- dashboards;
- documentação;
- deploy.

## Portfólio

O portfólio é diferente do GitHub. Ele mostra narrativa, imagens, resultados e explicação do problema.

O SotuHire pode sugerir:

- quais projetos colocar no topo;
- como descrever cada projeto;
- quais screenshots faltam;
- quais métricas destacar;
- como conectar projeto com a vaga.

## Perfil acadêmico vs perfil corporativo

| Tipo | Melhor para | Problema se usado errado |
|---|---|---|
| ATS Resume | vagas corporativas e plataformas | pode ficar genérico demais |
| Lattes | pesquisa, academia, bolsas, P&D | pode ser longo e pouco direto |
| LinkedIn | networking e recrutadores | pode ser informal ou incompleto |
| GitHub | vagas técnicas | nem todo recrutador lê código |
| Portfólio | demonstrar projetos | precisa de narrativa clara |

## Regras de recomendação

### Quando a vaga for estágio/júnior corporativo

Priorizar:

- currículo ATS;
- projetos aplicados;
- ferramentas;
- experiências práticas;
- formação;
- GitHub;
- LinkedIn.

Usar Lattes apenas para extrair itens relevantes.

### Quando a vaga for pesquisa, laboratório ou P&D

Priorizar:

- Lattes;
- projetos acadêmicos;
- publicações;
- iniciação científica;
- produção técnica;
- formação;
- ferramentas de pesquisa;
- GitHub quando houver código.

### Quando a vaga for IA/dados

Combinar:

- currículo ATS;
- GitHub;
- projetos;
- certificados;
- Lattes se houver pesquisa;
- palavras-chave da vaga.

## Scores sugeridos

O SotuHire pode separar scores:

```text
ats_score: legibilidade para ATS
match_score: aderência à vaga
academic_score: relevância acadêmica/Lattes
portfolio_score: força dos projetos
risk_score: risco de incompatibilidade
```

Isso evita dizer que uma pessoa tem “match baixo” só porque o currículo corporativo não mostra algo que está no Lattes ou GitHub.

## Campos extras no schema

Adicionar ao schema futuro:

```json
{
  "resume_type_detected": "ats_resume",
  "source_profiles_used": ["pdf_resume", "lattes", "github"],
  "ats_score": 78,
  "academic_score": 64,
  "portfolio_score": 82,
  "lattes_relevant_items": [],
  "github_relevant_projects": [],
  "recommended_resume_version": "ats_resume_for_data_internship"
}
```

## Privacidade

Dados de currículo são sensíveis.

Regras:

- não subir currículo para serviços desnecessários;
- não salvar currículo completo sem aviso;
- permitir apagar dados;
- evitar logs com conteúdo pessoal;
- mascarar e-mail/telefone em logs;
- não coletar Lattes/LinkedIn/GitHub sem ação do usuário;
- preferir entrada manual no MVP.

## MVP recomendado

Para o MVP inicial:

1. upload de currículo PDF;
2. campo opcional para texto do Lattes;
3. campo opcional para links GitHub/LinkedIn;
4. descrição da vaga;
5. análise estruturada;
6. recomendação de qual versão do currículo usar.

Não implementar scraping de Lattes no começo. Primeiro aceite o texto ou arquivo fornecido pelo usuário.
