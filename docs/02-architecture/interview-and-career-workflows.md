# Workflows de entrevista e carreira

O schema 7 persiste InterviewSession, InterviewPreparation, StarStory, InterviewQuestion, InterviewDraftAnswer, FollowUpDraft, CareerTask, Reminder e CareerPlan.

Preparação usa somente evidências confirmadas. História STAR gerada por IA não aceita resultado numérico sem `evidence_refs`; respostas preenchidas exigem evidência. Follow-up tem estados de draft/review/cópia/envio manual, sem sender.

Tarefas, lembretes e planos são locais. O export RFC 5545 gera arquivo ICS com CRLF e UID estável; não contém `METHOD` nem importa calendário automaticamente. Certificações exigem classificação e fonte oficial; projetos de gap são candidatos revisáveis.
