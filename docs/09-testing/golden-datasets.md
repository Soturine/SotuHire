# Golden datasets

## Finalidade

Golden datasets são conjuntos sintéticos e anonimizados usados para verificar extração, evidência, segurança, deduplicação e regressão. Eles não são exemplos promocionais: cada caso possui resposta esperada e fatos que o sistema está proibido de inventar.

## Estrutura proposta

```text
tests/fixtures/golden/
├── manifests/
├── resumes/
├── jobs/
├── lattes/
├── public_exams/
├── github/
├── extension/
├── deduplication/
└── expected/
```

Os fixtures atuais em `tests/fixtures/resumes`, `jobs`, `matching`, `github_repos`, `html` e `extension` podem ser referenciados; não devem ser duplicados sem motivo.

## Segmentos obrigatórios

| Segmento | Casos mínimos |
| --- | --- |
| Tecnologia e dados | backend, dados, segurança, repositório incompleto |
| Engenharia/técnico | civil, biomédica, manutenção, registro a confirmar |
| Saúde | enfermagem e requisito de conselho sem confirmação automática |
| Educação | licenciatura, docência, extensão e experiência informal |
| Pesquisa | Lattes, DOI, ORCID, publicação e projeto |
| Direito | formação, OAB a confirmar e vaga sem evidência suficiente |
| Administração/serviços | operações, atendimento, turismo e skills transferíveis |
| Artes/design | portfólio, projeto visual e ausência de GitHub |
| Transição | evidência transferível sem inventar experiência no cargo-alvo |
| Editais | datas, taxa, cargo, documentos, requisitos e versões duplicadas |

## Regras de anotação

- todo fato esperado aponta para trecho ou referência;
- ausência de evidência produz `uncertain`/warning, não claim positivo;
- dados sensíveis são fictícios e marcados;
- nomes, organizações, URLs e documentos não pertencem a pessoas reais;
- variações de acento/caixa podem ser equivalentes após normalização;
- datas, números e registros exigem correspondência exata;
- duplicata incerta deve ser sugestão, nunca merge automático;
- alterações de conteúdo geram novo snapshot/hash.

## Versionamento

Cada manifest deve registrar `dataset_version`, hash dos arquivos, schema esperado e commit de criação. Mudança de gold exige revisão separada de mudança de modelo/prompt para evitar “corrigir o teste” em favor da saída atual.

## Privacidade e segurança

Não incluir:

- currículos ou editais pessoais reais;
- e-mails, telefones, documentos ou endereços reais;
- chaves, tokens, cookies ou sessões;
- dumps de storage da extensão;
- respostas externas que reproduzam dados privados.

Testes externos são opt-in e skipped sem variável local. O CI padrão usa somente mocks e fixtures versionados.

## Estado desta fundação

O repositório já possui fixtures multiárea úteis, mas ainda não possui manifests anotados completos nem baseline estatístico. A próxima etapa deve selecionar os fixtures existentes, criar gold facts/evidence e medir o caminho local antes de comparar providers.
