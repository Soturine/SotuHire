# Conectores de fontes

## Objetivo

Este documento organiza quais fontes o SotuHire pode integrar e como cada uma deve ser tratada.

A regra principal é:

> Cada fonte deve virar um conector isolado que retorna o mesmo schema de vaga.

Isso evita espalhar lógica de scraping pela aplicação inteira.

## Interface conceitual

```python
class JobSourceConnector:
    name: str

    def search(self, query: JobSearchQuery) -> list[RawJob]:
        ...

    def normalize(self, raw_job: RawJob) -> NormalizedJob:
        ...
```

## Tipos de fonte

### 1. Entrada manual

Fonte mais importante no começo.

Entradas:

- descrição colada;
- post colado;
- link colado;
- arquivo JSON;
- arquivo CSV.

Vantagem: permite testar o matcher sem depender de scraper.

### 2. ATS / job boards públicos

Fontes possíveis:

- Greenhouse;
- Lever;
- Ashby;
- Gupy;
- InHire;
- Vagas.com;
- Programathor;
- Remotar;
- páginas públicas de empresas;
- páginas de programas de estágio;
- CIEE;
- Companhia de Estágios;
- Cia de Talentos;
- Nube;
- 99jobs;
- Eureca.

Essas fontes devem ser avaliadas caso a caso.

### 3. Agregadores de vagas

Possíveis fontes:

- Indeed Brasil;
- InfoJobs;
- Catho;
- Trabalha Brasil;
- BNE;
- sites regionais;
- newsletters públicas.

Exigem cuidado porque podem ter termos próprios, bloqueios e estruturas variáveis.

### 4. Posts e conteúdo informal

Entradas:

- texto colado pelo usuário;
- post público salvo manualmente;
- newsletter;
- comunidade;
- thread pública;
- página de recrutador.

O Hidden Jobs Radar entra aqui.

## Política por fonte

Cada fonte deve ter um arquivo de configuração:

```yaml
source: "example"
enabled: true
type: "public_page"
requires_login: false
allowed_collection: true
rate_limit_seconds: 3
max_pages_per_run: 20
robots_txt_required: true
notes: "Only public job pages."
```

## Estados de uma fonte

```text
manual_only
planned
experimental
active
paused
blocked
deprecated
```

Exemplo:

```text
LinkedIn: manual_only
Greenhouse: planned
Lever: planned
Company pages: experimental
Gupy: planned
InfoJobs: planned
Indeed Brasil: planned
CIEE: planned
Companhia de Estágios: experimental
InHire: planned_dynamic
Vagas.com: planned
Catho: planned
Generic public pages: active
```

## LinkedIn

LinkedIn deve ser tratado como fonte **manual/assistiva** no SotuHire.

Permitido no produto:

- usuário colar texto de vaga;
- usuário colar texto de post;
- usuário colar link para registro;
- usuário usar uma extensão local para enviar o texto da página aberta ao SotuHire, se implementado com limites claros.

Não implementar:

- login automático;
- scraping de perfis;
- scraping de feed autenticado em massa;
- envio automático de mensagens;
- candidatura automática;
- bypass de limites.

## Greenhouse / Lever / Ashby

São boas fontes candidatas para o futuro porque muitas empresas usam páginas públicas de vagas. A implementação deve começar com links de empresas específicas e não com varredura global.

Exemplo de abordagem:

1. usuário cadastra uma empresa/fonte;
2. sistema coleta vagas daquela página pública;
3. normaliza os dados;
4. calcula match;
5. salva no histórico.

## Gupy

A Gupy é relevante no Brasil, mas deve ser analisada com cuidado por causa de estrutura, termos e eventuais limitações técnicas. Para MVP, o melhor é aceitar link ou descrição colada. O conector automático pode entrar depois.

## Páginas de carreira de empresas

Bom ponto inicial para scraping.

Exemplos de campos:

- título;
- departamento;
- localização;
- modalidade;
- descrição;
- requisitos;
- link de aplicação.

## Programas de estágio

O SotuHire deve ter um modo especial para programas de estágio/trainee, pois são muito relevantes para o público-alvo.

Campos úteis:

- nome do programa;
- empresa;
- prazo de inscrição;
- áreas aceitas;
- requisitos de curso;
- período mínimo;
- localidade;
- modalidade;
- link.


## Portais brasileiros específicos

A matriz completa está em [`brazilian-job-portals.md`](brazilian-job-portals.md).

Conectores prioritários por valor para o público-alvo:

1. Gupy;
2. LinkedIn em modo manual/assistivo;
3. CIEE;
4. Companhia de Estágios;
5. InfoJobs;
6. Indeed Brasil;
7. InHire;
8. Vagas.com;
9. Catho;
10. Cia de Talentos/Nube/99jobs/Eureca para programas de entrada.

Esses conectores não devem compartilhar código improvisado. Cada fonte deve ter parser, normalizador, testes e política própria.

## Normalização de senioridade

Cada fonte escreve senioridade de um jeito. O conector deve normalizar:

```text
estágio -> internship
intern -> internship
trainee -> trainee
júnior -> junior
jr -> junior
pleno -> mid
sênior -> senior
specialist -> specialist
tech lead -> lead
```

## Normalização de modalidade

```text
remoto -> remote
híbrido -> hybrid
presencial -> onsite
home office -> remote
anywhere -> remote
```

## Normalização de localidade

Separar:

- cidade;
- estado;
- país;
- remoto nacional;
- remoto global;
- híbrido com cidade;
- presencial.

## Erros por fonte

Cada conector deve retornar erros controlados, não quebrar o app inteiro.

```python
class SourceError:
    source: str
    url: str
    error_type: str
    message: str
    recoverable: bool
```

## Testes

Cada conector deve ter fixtures:

```text
tests/fixtures/sources/
├── greenhouse_sample.html
├── lever_sample.html
├── company_page_sample.html
└── hidden_post_sample.txt
```

Testes:

- extrai título;
- extrai empresa;
- extrai local;
- extrai descrição;
- normaliza senioridade;
- não quebra com campo ausente;
- ignora vaga sem título.

---

# Contrato expandido de conectores

Conectores devem implementar uma interface comum.

```python
class JobSourceConnector:
    source_name: str
    access_mode: str

    def search(self, query: JobSearchQuery) -> list[JobPosting]:
        ...

    def parse(self, raw: str) -> list[JobPosting]:
        ...
```

## Conectores planejados

- `ManualConnector`
- `LinkedInManualConnector`
- `GupyConnector`
- `InfoJobsConnector`
- `IndeedConnector`
- `CieeConnector`
- `CompanhiaEstagiosConnector`
- `InHireConnector`
- `RemotarConnector`
- `MeuHomeConnector`
- `GreenhouseConnector`
- `LeverConnector`
- `AshbyConnector`

## Status possíveis

```text
manual_only
planned
experimental
active
paused
blocked
deprecated
```

## Testes obrigatórios

- parse com HTML fixture;
- normalização de campos;
- deduplicação;
- erro de rede;
- fonte sem resultado;
- fonte com layout alterado;
- limite de rate.
