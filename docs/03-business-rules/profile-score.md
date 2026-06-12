# Profile Score Engine

O **Profile Score Engine** avalia a presença profissional do usuário além do currículo.

Ele junta sinais de:

- currículo ATS;
- Currículo Lattes;
- LinkedIn;
- GitHub;
- portfólio;
- artigos;
- projetos;
- pacotes publicados;
- histórico de candidatura.

## Scores principais

```text
ATS Score        -> qualidade do currículo para sistemas de triagem.
Match Score      -> compatibilidade com uma vaga específica.
Risk Score       -> risco de incompatibilidade, golpe, senioridade errada ou fonte ruim.
LinkedIn Score   -> força do perfil para recrutadores.
Portfolio Score  -> força dos projetos e presença técnica.
Lattes Score     -> relevância acadêmica quando fizer sentido.
Readiness Score  -> prontidão geral para aplicar agora.
```

## LinkedIn Score

Inspirado em projetos que analisam exportações oficiais do LinkedIn por CSV, o SotuHire deve preferir entrada segura:

- usuário exporta os dados oficialmente;
- usuário envia os CSVs localmente;
- SotuHire calcula score;
- SotuHire gera recomendações.

Referência de inspiração: [linkedin-profile-score](https://github.com/henriquesantanati/linkedin-profile-score).

### Critérios

- headline contém cargo-alvo e keywords;
- about explica objetivo e stack;
- experiências têm impacto e tecnologias;
- skills combinam com vagas alvo;
- formação está coerente;
- certificados relevantes aparecem;
- perfil está consistente com currículo;
- URL, foto, banner e destaque são avaliados via checklist manual.

## Portfolio Score

Avalia se os projetos públicos ajudam a candidatura.

Critérios:

- README claro;
- instalação local documentada;
- screenshots ou demo;
- testes;
- CI;
- licença;
- estrutura de pastas;
- tecnologias relevantes;
- commits reais;
- issues/roadmap;
- deploy;
- documentação técnica;
- alinhamento com vaga.

## Lattes Score

Currículo Lattes não é currículo ATS. Ele deve ser tratado como fonte acadêmica.

O SotuHire deve extrair:

- formação;
- iniciação científica;
- publicações;
- eventos;
- projetos;
- orientações;
- cursos;
- áreas de pesquisa;
- produção técnica.

Depois deve converter esses sinais para versões úteis:

- currículo ATS;
- resumo profissional;
- perfil acadêmico;
- evidências para vagas de pesquisa, dados, IA, educação, laboratório ou estágio.

## Readiness Score

O Readiness Score responde:

```text
Vale aplicar agora ou ajustar antes?
```

Exemplo:

```json
{
  "readiness_score": 76,
  "apply_now": true,
  "needs_adjustment": [
    "melhorar headline do LinkedIn",
    "adicionar SQL no resumo do currículo",
    "destacar projeto GitHub relacionado"
  ]
}
```

## Regras de negócio

- Score não pode ser usado como verdade absoluta.
- Score deve explicar evidências.
- Score deve separar ausência de dados de desempenho ruim.
- Score não deve incentivar mentira.
- Score deve proteger dados pessoais.
- Score deve permitir modo local-first.

## Relação com outros docs

- [Resume Types](./resume-types.md)
- [Matching Rules](./matching-rules.md)
- [ATS Rules](./ats-rules.md)
- [RAG Memory Architecture](../04-ai/rag-memory-architecture.md)
- [GitHub Portfolio Analyzer](../05-data-sources/github-portfolio-analyzer.md)
