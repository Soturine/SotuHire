# Fundação para Editais e Concursos

A v1.9.3 implementa a primeira fundação real para editais, concursos públicos, processos seletivos públicos, bolsas, residências, estágios públicos e chamadas institucionais.

Ela ainda não é um sistema completo de concursos. O objetivo é criar uma base limpa, testável, local-first e evolutiva para interpretar editais por texto colado, comparar requisitos com o Perfil Profissional Universal e gerar um plano inicial de estudo.

> O SotuHire ajuda a organizar e interpretar editais, mas o edital oficial sempre prevalece. Revise manualmente requisitos, datas, taxa, documentos, conteúdo programático e regras da banca.

## Por que é um domínio separado

Edital não é vaga privada. Concurso tem regras próprias: órgão, banca, cargo, requisitos legais, datas, taxa, conteúdo programático, etapas, prova, títulos e documentos.

Por isso a implementação fica em `modules/public_exams/`, separada de `modules/radar`, `modules/profile` e `modules/tracker`.

## Módulo

```text
modules/public_exams/
  __init__.py
  models.py
  parser.py
  service.py
  scoring.py
  store.py
  study_plan.py
  formatters.py
```

Modelos principais:

- `ExamNotice`: edital/processo seletivo, com órgão, banca, taxa, timeline, cargos, documentos, requisitos e warnings.
- `ExamRole`: cargo/função/vaga pública, com escolaridade, registro, salário, vagas, lotação, requisitos, etapas e conteúdo.
- `ExamRequirement`: requisito legal/documental/acadêmico, com status `matched`, `missing` ou `uncertain`.
- `ExamTimeline`: inscrições, pagamento, prova, resultado, recursos e outras datas.
- `ExamSubject`: disciplina, tópicos, etapa, peso/questões quando disponíveis e prioridade.
- `ExamFitScore`: score inicial conservador entre edital/cargo e Perfil Universal.
- `StudyPlanDraft`: plano inicial simples, por prioridade ou por calendário quando há data de prova.

## Fluxo de importação

Entrada:

```json
{
  "text": "texto colado do edital",
  "source_url": "opcional",
  "source_name": "opcional",
  "use_ai": false,
  "language": "pt-BR"
}
```

Saída:

```json
{
  "notice": {},
  "roles": [],
  "timeline": {},
  "subjects": [],
  "requirements": [],
  "warnings": [],
  "needs_user_review": true,
  "provider_used": "local",
  "analysis_mode": "local"
}
```

O endpoint de importação retorna somente rascunho. Nada é salvo até a chamada explícita de confirmação.

## API

```text
POST   /api/v1/public-exams/import
GET    /api/v1/public-exams
GET    /api/v1/public-exams/{notice_id}
DELETE /api/v1/public-exams/{notice_id}
POST   /api/v1/public-exams/{notice_id}/confirm
POST   /api/v1/public-exams/{notice_id}/analyze
POST   /api/v1/public-exams/{notice_id}/study-plan
```

## Parser local

O parser local detecta, de forma conservadora:

- órgão/instituição;
- banca organizadora;
- número do edital;
- cargo/função;
- nível e escolaridade;
- registro profissional como CREA, CFT, CRQ, COREN, CRP, CRM, OAB, CRC e CAU;
- salário, vencimento ou bolsa;
- taxa de inscrição;
- carga horária, vagas e cadastro reserva;
- local de prova ou lotação;
- inscrição, pagamento, prova, resultado e recursos;
- requisitos gerais;
- documentos exigidos;
- etapas como prova objetiva, discursiva, prática, títulos, TAF e avaliação médica/psicológica;
- conteúdo programático.

Warnings aparecem quando faltam datas, requisitos, salário/taxa, conteúdo programático ou quando o texto parece curto/truncado.

## IA opcional

O prompt `public_exam_notice_extractor_v1` pode estruturar o edital com Gemini ou OpenAI quando configurado no backend local.

Regras:

- a IA usa somente o texto colado;
- a IA não inventa órgão, banca, datas, taxa, salário, requisito ou conteúdo programático;
- a resposta sempre exige `needs_user_review=true`;
- rascunho vazio ou inválido cai para parser local;
- nenhum dado sensível ou chave de provider vai para o frontend.

Na v1.9.4, o endpoint de importação também registra `requested_provider`, `provider_used` e `analysis_mode`. O provider usa o modelo salvo em Configurações de IA. Se a chamada externa falhar, o draft volta ao parser local e permanece com `needs_user_review=true`.

Capturas da extensão com `kind=public_exam` podem abrir `/public-exams?capture_id=...` e virar rascunho revisável. A captura não é salva como vaga privada e não gera inscrição/candidatura automática.

## Perfil, Lattes e contexto

A análise usa o Perfil Profissional Universal e o Career Context Engine com `purpose=public_exams`.

Entram como evidências:

- formação acadêmica confirmada;
- curso em andamento/concluído;
- registros profissionais confirmados;
- certificações;
- experiência profissional;
- preferências de localidade, contrato e disponibilidade;
- evidências acadêmicas/Lattes já confirmadas, como pesquisa, extensão, docência, publicações, bolsas e produção técnica.

Regra crítica: edital não adiciona formação, registro ou certificação ao Perfil. Ele apenas compara requisitos com evidências já existentes.

## Exam Fit Score

O `ExamFitScore` calcula uma pontuação inicial, nunca uma decisão final de elegibilidade.

Componentes:

- requisitos obrigatórios;
- timeline e prazos;
- localidade;
- salário/bolsa;
- esforço de estudo;
- alinhamento com objetivos do Perfil;
- risco por lacunas ou incertezas.

Recomendações possíveis:

- `strong_fit`;
- `good_fit`;
- `review_requirements`;
- `risky`;
- `not_recommended`;
- `insufficient_information`.

Linguagem esperada: "parece compatível", "há evidência", "precisa confirmar". O sistema não deve dizer "apto" de forma absoluta.

## Radar e Tracker

Radar e Tracker ficam preparados para oportunidades públicas sem misturar com vagas privadas:

```text
job
public_exam
academic_call
scholarship
residency
internship_public
```

Status públicos preparados:

```text
noticed
reviewing_notice
requirements_review
registered_manually
studying
exam_scheduled
document_pending
result_waiting
approved
rejected
archived
```

Na v1.9.3 não há crawler de editais, busca automática na internet ou inscrição automatizada.

## Limites de segurança

- Sem inscrição automática.
- Sem pagamento automático.
- Sem emissão automática de boleto.
- Sem envio automático de documentos.
- Sem login em banca/órgão.
- Sem scraping autenticado.
- Sem crawler logado.
- Sem CAPTCHA bypass.
- Sem captura de cookies, tokens, sessão, headers ou storage.
- Sem API key do app no frontend.
- Sem decisão crítica salva apenas por IA.
- Sem alteração no `/api/v1/sources/authenticated-browser/collect`.

## Próximos passos

- Upload seguro de PDF/HTML.
- Parsers por banca.
- Comparação edital antigo vs novo.
- Histórico de chamadas/convocações.
- Radar público automático seguro.
- Plano de estudo avançado.
