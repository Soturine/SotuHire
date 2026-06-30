# Fundação para Editais e Concursos

A v1.9.2 prepara a base documental para concursos, editais, bolsas e chamadas públicas, mas não implementa o Concurso Mode completo.

## Por que é um domínio separado

Um edital não é uma vaga privada. Ele traz regras formais, requisitos eliminatórios, etapas, banca, cronograma, documentos, conteúdo programático, títulos, critérios de desempate e riscos jurídicos/administrativos. Por isso, o SotuHire deve tratar esse domínio em módulos próprios, sem misturar regras de ATS corporativo com regras de concurso.

## Entidades futuras

- `ExamNotice`: edital, órgão, banca, URL e versão.
- `ExamRole`: cargo, área, regime, localidade e remuneração.
- `ExamRequirement`: formação, registro, experiência, título ou documento exigido.
- `ExamSubject`: disciplina, tópico e peso.
- `ExamTimeline`: inscrição, pagamento, prova, resultado e recursos.
- `ExamFitScore`: aderência ao Perfil Profissional Universal.
- `StudyPlanDraft`: plano de estudos revisável por disciplina.

## Relação com o Perfil Profissional Universal

O futuro parser de edital deve consultar o Perfil Profissional Universal e o Career Context Engine para verificar:

- formação acadêmica;
- registros profissionais;
- titulações;
- produção científica, técnica ou artística;
- experiência docente, de pesquisa, extensão, laboratório, campo ou clínica;
- restrições de localidade, carga horária e disponibilidade.

Evidências vindas de Lattes entram no mesmo Perfil Universal, não em um perfil separado.

## Limites de segurança

- Não faz inscrição automática.
- Não substitui leitura jurídica do edital.
- Não faz login em plataformas de concurso.
- Não captura cookies, tokens, sessão, headers ou storage de terceiros.
- Não decide elegibilidade final sem revisão humana.
- Não promete aprovação.

## Escopo da v1.9.2

A v1.9.2 apenas documenta a fundação, reforça o Perfil acadêmico/Lattes e prepara o contexto para futuras análises de editais. O parser real de edital, ranking de concursos e plano de estudo podem entrar em ciclo posterior.
