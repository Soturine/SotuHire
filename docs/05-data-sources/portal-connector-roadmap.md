# Roadmap de conectores de portais

## Objetivo

Este documento transforma a lista de fontes em um plano técnico de implementação.

A meta é evitar overengineering e, ao mesmo tempo, preparar o SotuHire para crescer de forma organizada.

## Princípio

O SotuHire deve começar com entrada manual e evoluir para conectores testáveis.

Não implementar todos os portais de uma vez.

## Estados dos conectores

```text
manual_only        -> só aceita texto/link colado
planned            -> fonte relevante, mas sem código ainda
experimental       -> conector inicial em teste
active             -> conector estável e testado
paused             -> temporariamente desativado
blocked            -> não deve ser usado por risco/termos/limite técnico
deprecated         -> fonte removida ou substituída
```

## Tipos de conectores

### ManualConnector

Recebe texto ou link colado pelo usuário.

Deve existir desde o MVP.

### PublicPageConnector

Lê uma página pública simples com HTTPX/Requests + BeautifulSoup.

### DynamicPublicPageConnector

Usa Playwright para página pública que depende de JavaScript.

Deve ser exceção.

### AtsPortalConnector

Conector para plataformas de recrutamento/ATS quando houver página pública estável.

Exemplos:

- Gupy;
- Greenhouse;
- Lever;
- Ashby;
- InHire, quando aplicável.

### InternshipProgramConnector

Conector especializado em programas de estágio, trainee e jovem aprendiz.

Exemplos:

- CIEE;
- Companhia de Estágios;
- Cia de Talentos;
- Nube;
- 99jobs;
- Eureca.

### AggregatorConnector

Conector para agregadores de vagas.

Exemplos:

- Indeed;
- InfoJobs;
- Catho;
- Trabalha Brasil;
- BNE.

Deve ter deduplicação forte.

## Prioridade realista

### v0.1

Sem scraping automático.

- `ManualConnector`;
- upload de currículo;
- colagem de vaga;
- análise de match.

### v0.2

Classificação da fonte manual.

Se o usuário colar um link, o sistema detecta:

```text
gupy.io -> Gupy
linkedin.com -> LinkedIn
infojobs.com.br -> InfoJobs
br.indeed.com -> Indeed
portal.ciee.org.br -> CIEE
ciadeestagios.com.br -> Companhia de Estágios
inhire.app -> InHire
vagas.com.br -> Vagas.com
catho.com.br -> Catho
```

### v0.3

Normalização de dados.

Criar:

```text
modules/sources/normalizer.py
modules/sources/source_registry.py
modules/sources/manual.py
```

### v0.4

Primeiro conector público simples.

Escolher uma fonte com baixo risco, por exemplo:

- página de carreira própria de empresa;
- página pública de programa de estágio;
- página estática salva como fixture.

### v0.5

Deduplicação e histórico.

Criar:

- hash de URL;
- hash de conteúdo;
- comparação por título/empresa/local;
- histórico SQLite.

### v0.6

Conectores de programas de estágio.

Priorizar:

- Companhia de Estágios;
- CIEE em modo assistivo/manual;
- Cia de Talentos;
- Nube.

### v0.7

Conectores ATS públicos.

Priorizar:

- Greenhouse;
- Lever;
- Ashby;
- Gupy por links públicos específicos.

### v0.8

Agregadores.

Adicionar com cuidado:

- Indeed;
- InfoJobs;
- Catho;
- Trabalha Brasil;
- BNE.

### v0.9

Extensão assistiva.

Permite enviar o conteúdo da página aberta para o SotuHire local, sem clicar em candidatura e sem rodar automação em massa.

## Source Registry

O projeto deve ter uma tabela central de fontes.

```python
SOURCE_REGISTRY = {
    "linkedin": {
        "display_name": "LinkedIn",
        "category": "social_jobs",
        "status": "manual_only",
        "priority": "high",
        "domains": ["linkedin.com"],
    },
    "gupy": {
        "display_name": "Gupy",
        "category": "ats_portal",
        "status": "planned",
        "priority": "high",
        "domains": ["gupy.io", "portal.gupy.io"],
    },
    "ciee": {
        "display_name": "CIEE",
        "category": "internship_program",
        "status": "planned",
        "priority": "high",
        "domains": ["portal.ciee.org.br", "ciee.app"],
    },
}
```

## Contrato mínimo de um conector

```python
class SourceConnector:
    source_key: str

    def can_handle(self, url: str) -> bool:
        ...

    def fetch(self, url: str) -> RawSourceDocument:
        ...

    def parse(self, document: RawSourceDocument) -> list[RawOpportunity]:
        ...

    def normalize(self, raw: RawOpportunity) -> NormalizedJob:
        ...
```

## Erros padronizados

```python
class SourceError(Exception):
    source_key: str
    url: str
    error_type: str
    recoverable: bool
```

Tipos de erro:

```text
network_error
blocked_by_source
requires_login
invalid_html
missing_required_field
unsupported_source
rate_limited
parser_broken
```

## Fixtures

Cada conector precisa de fixtures.

```text
tests/fixtures/sources/
├── gupy_job_sample.html
├── ciee_public_vitrine_sample.html
├── companhia_de_estagios_program_sample.html
├── infojobs_job_sample.html
├── indeed_job_sample.html
├── inhire_dynamic_sample.html
└── linkedin_pasted_post_sample.txt
```

## Critério de qualidade

Um conector só é aceitável quando:

- tem teste;
- não quebra a aplicação inteira;
- salva logs;
- respeita rate limit;
- não depende de credenciais pessoais;
- retorna schema normalizado;
- tem documentação de limitações.

## O que evitar

Evitar:

- um crawler genérico tentando ler qualquer coisa;
- Playwright para tudo;
- Scrapy antes de precisar;
- scraping logado;
- automação de candidatura;
- conector sem teste;
- regra de parsing espalhada pela UI.
