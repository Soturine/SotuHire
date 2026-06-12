# Portais brasileiros de vagas e programas de estágio

## Objetivo

Este documento expande a estratégia de fontes do SotuHire para o contexto brasileiro.

O SotuHire deve entender que o mercado brasileiro não depende só de LinkedIn. Muitas oportunidades aparecem em portais específicos, ATS corporativos, agentes de integração de estágio, páginas de programas, newsletters e posts de recrutadores.

## Regra principal

Cada portal deve ser tratado como uma fonte com política própria.

O SotuHire não deve assumir que todo site pode ser raspado automaticamente. Para cada fonte, o sistema deve definir:

- se é entrada manual, conector público, conector experimental ou bloqueado;
- se exige login;
- se há página pública de vagas;
- se há risco de termos de uso;
- se o conteúdo é estático ou dinâmico;
- se precisa de Playwright;
- se vale começar com link/descrição colada;
- quais campos podem ser normalizados.

## Matriz de fontes brasileiras

| Fonte | Tipo | Prioridade | Melhor abordagem inicial | Observação |
|---|---|---:|---|---|
| LinkedIn | rede social + vagas | Alta | manual/assistiva | colar vaga/post/link; extensão local no futuro; evitar bot logado |
| Gupy | ATS / portal de vagas | Alta | link/descrição + conector planejado | muito comum no Brasil; analisar páginas públicas caso a caso |
| InfoJobs | job board | Alta | busca manual + link/descrição | agregador grande; cuidado com termos e estrutura |
| Indeed Brasil | agregador/buscador | Alta | busca manual + link/descrição | indexa vagas de várias fontes; deduplicação é essencial |
| CIEE | estágio/aprendiz | Alta | conector planejado + manual | muito relevante para estágio e jovem aprendiz |
| Companhia de Estágios | estágio/trainee/aprendiz | Alta | conector experimental | possui páginas públicas de programas e inscrições |
| InHire | ATS / R&S | Média | manual + Playwright apenas se necessário | site depende de JavaScript; avaliar por página pública de empresa |
| Vagas.com | ATS/job board | Média/Alta | manual + conector planejado | forte no Brasil; também possui IA/currículo |
| Catho | job board | Média | manual + conector planejado | portal amplo; pode exigir cadastro em fluxos de candidatura |
| Cia de Talentos | programas de estágio/trainee | Média/Alta | manual + conector por programa | relevante para programas de entrada |
| Nube | estágio/aprendiz | Média/Alta | manual + conector planejado | forte para estágio |
| 99jobs | programas e cultura | Média | manual + conector planejado | útil para estágio/trainee e empresas específicas |
| Eureca | programas de entrada | Média | manual + conector planejado | costuma ter processos seletivos e programas jovens |
| Trabalha Brasil | job board | Média | manual + conector experimental | agregador nacional |
| BNE | job board | Média | manual + conector experimental | agregador nacional |
| Glassdoor | vagas + reviews | Baixa/Média | manual | reviews podem ser úteis, mas não são foco do MVP |
| Remotar | remoto | Média | conector planejado | útil para vagas remotas |
| Programathor | tecnologia | Média/Alta | conector planejado | útil para dev/tech |
| Greenhouse | ATS global | Alta | conector planejado | muitas páginas públicas e previsíveis |
| Lever | ATS global | Alta | conector planejado | muitas páginas públicas e previsíveis |
| Ashby | ATS global | Alta | conector planejado | muitas páginas públicas modernas |
| Sites de empresas | carreira própria | Alta | conector público simples | melhor início para scraping responsável |
| Universidades/faculdades | murais de vagas | Média | manual + páginas públicas | útil para estágio local |
| Newsletters | vagas curadas | Média | entrada manual/RSS se existir | boa fonte para Hidden Jobs Radar |
| Telegram/Discord/WhatsApp | comunidades | Média | texto exportado/colado | não coletar grupos privados automaticamente |

## Estratégia por fonte

### LinkedIn

LinkedIn é importante, mas deve ser tratado com cuidado.

Permitido:

- usuário colar descrição da vaga;
- usuário colar post público;
- usuário salvar link;
- extensão local enviar o texto da página aberta pelo usuário;
- análise de match e mensagem para recrutador.

Não implementar:

- login automático;
- scraping de feed autenticado;
- scraping de perfis em massa;
- envio automático de mensagens;
- candidatura automática;
- download de contatos.

Status recomendado:

```yaml
source: linkedin
status: manual_only
priority: high
connector: extension_assistive_future
```

### Gupy

Gupy é uma das fontes mais importantes para o Brasil.

Abordagem recomendada:

1. aceitar link/descrição colada no MVP;
2. salvar URL da vaga;
3. normalizar empresa, cargo, local e requisitos;
4. estudar páginas públicas de vagas por empresa;
5. só depois criar conector automático.

Campos úteis:

- título;
- empresa;
- localidade;
- modelo de trabalho;
- requisitos;
- responsabilidades;
- etapas do processo;
- link de candidatura;
- prazo, se houver.

Status:

```yaml
source: gupy
status: planned
priority: high
initial_mode: manual_url_and_text
```

### InfoJobs

InfoJobs é útil como job board amplo.

Abordagem:

- começar com link/descrição colada;
- permitir busca manual externa;
- normalizar dados;
- criar conector apenas se a estrutura pública for estável e permitida.

Pontos de atenção:

- muitas vagas duplicadas;
- qualidade variável;
- alguns fluxos podem exigir login;
- descrição pode vir com ruído.

### Indeed Brasil

Indeed funciona como agregador/buscador de vagas.

Abordagem:

- usar como fonte de descoberta manual no começo;
- salvar URL e descrição;
- deduplicar fortemente;
- preferir página original da empresa quando possível.

Pontos de atenção:

- a mesma vaga pode aparecer no Indeed, Gupy e site da empresa;
- o link pode redirecionar;
- algumas candidaturas passam pelo próprio Indeed;
- pode haver bloqueios ou termos específicos.

### CIEE

CIEE é essencial para estágio e jovem aprendiz.

Abordagem:

- priorizar no radar de estágio;
- permitir filtro por tipo: estágio, aprendiz, processos públicos;
- começar com busca manual e link;
- estudar vitrine pública de vagas;
- não tentar acessar área logada automaticamente.

Campos úteis:

- tipo de vaga;
- nível de ensino;
- curso;
- cidade;
- código da vaga;
- empresa, quando visível;
- bolsa/benefícios, se visíveis;
- link/código para candidatura.

Status:

```yaml
source: ciee
status: planned
priority: high
initial_mode: manual_and_public_vitrine
```

### Companhia de Estágios

Companhia de Estágios é forte para estágio, trainee e jovem aprendiz.

Abordagem:

- bom candidato para conector experimental;
- muitas oportunidades aparecem como programas públicos;
- extrair nome do programa, empresa, status de inscrição e link.

Campos úteis:

- nome do programa;
- empresa;
- tipo: estágio, trainee, aprendiz;
- status: aberto/encerrado;
- link de inscrição;
- requisitos;
- localização;
- cursos aceitos.

Status:

```yaml
source: companhia_de_estagios
status: experimental
priority: high
initial_mode: public_program_pages
```

### InHire

InHire deve ser tratado como fonte dinâmica.

O site principal pode depender de JavaScript, então o SotuHire não deve começar tentando crawler genérico.

Abordagem:

- aceitar link/descrição colada;
- se uma empresa usar InHire com página pública estável, estudar caso a caso;
- usar Playwright apenas quando o conteúdo for público e realmente depender de JS;
- não acessar área privada ou login.

Status:

```yaml
source: inhire
status: planned_dynamic
priority: medium
initial_mode: manual_url_and_text
```

### Vagas.com

Vagas.com é relevante porque mistura portal, ATS e currículo.

Abordagem:

- começar com link/descrição colada;
- estudar páginas públicas;
- manter status planejado;
- usar como referência de features de IA/currículo.

### Catho

Catho é amplo e útil para busca geral, mas não deve ser prioridade máxima para estágio/IA.

Abordagem:

- link manual;
- descrição colada;
- conector futuro somente se houver valor claro.

### Cia de Talentos, Nube, 99jobs e Eureca

Essas fontes são muito relevantes para programas de entrada.

O SotuHire deve tratá-las como categoria:

```text
programas_de_entrada
```

Campos especiais:

- nome do programa;
- período de inscrição;
- requisitos de graduação;
- cursos aceitos;
- localidade;
- trilhas/áreas;
- etapas do processo;
- link de inscrição.

## Ordem recomendada de implementação

### Fase 1 — Entrada manual e links

Implementar suporte para:

- LinkedIn;
- Gupy;
- InfoJobs;
- Indeed;
- CIEE;
- Companhia de Estágios;
- InHire;
- Vagas.com;
- Catho;
- Programathor;
- Remotar.

Nesta fase, o sistema não coleta automaticamente. Ele apenas recebe texto/link e classifica a fonte.

### Fase 2 — Páginas públicas simples

Implementar conectores para:

- sites de carreira de empresas;
- páginas públicas de programas de estágio;
- Companhia de Estágios, se a página continuar estável;
- Remotar/Programathor, se permitido e simples;
- Greenhouse/Lever/Ashby por empresa.

### Fase 3 — ATS e portais brasileiros

Implementar conectores específicos para:

- Gupy;
- CIEE;
- Vagas.com;
- InfoJobs;
- Indeed;
- InHire, se houver páginas públicas estáveis.

Cada conector precisa de testes com fixtures.

### Fase 4 — Hidden Jobs Radar

Adicionar:

- posts colados;
- newsletters;
- comunidades;
- textos de recrutadores;
- e-mails de vagas encaminhados pelo usuário;
- prints convertidos em texto apenas quando necessário.

## Schema de fonte

```json
{
  "source_name": "Gupy",
  "source_key": "gupy",
  "source_category": "ats_portal",
  "collection_mode": "manual_url_and_text",
  "requires_login": false,
  "supports_public_pages": true,
  "connector_status": "planned",
  "risk_level": "medium",
  "priority": "high",
  "notes": "Start with pasted URL and job text. Automatic connector only after source evaluation."
}
```

## Testes por portal

Cada portal deve ter testes como:

- normaliza nome da fonte;
- detecta tipo de vaga;
- extrai cargo;
- extrai empresa;
- extrai localidade;
- extrai modelo de trabalho;
- detecta senioridade;
- detecta estágio/aprendiz/trainee;
- não quebra com campo ausente;
- gera erro controlado quando a página muda.

## Não transformar em bagunça

O SotuHire não deve ter um arquivo gigante chamado `scraper.py`.

Estrutura recomendada:

```text
modules/sources/
├── base.py
├── manual.py
├── normalizer.py
├── deduplication.py
├── portals/
│   ├── gupy.py
│   ├── ciee.py
│   ├── companhia_de_estagios.py
│   ├── infojobs.py
│   ├── indeed.py
│   └── inhire.py
└── fixtures/
```

## Critério para ativar um portal

Um portal só deve sair de `planned` para `active` quando:

- há teste automatizado;
- há fixture salva;
- há rate limit;
- há tratamento de erro;
- há deduplicação;
- não depende de login;
- não faz bypass;
- não coleta dados pessoais desnecessários;
- não gera candidatura automática.
