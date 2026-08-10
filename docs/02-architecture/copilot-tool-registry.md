# Copilot Tool Registry

Cada tool declara ID, descrição, input/output schema, read-only, approval, risco, domínio, categoria
e handler. O registry recusa tool desconhecida e write sem `requires_approval=true`.

Disponíveis: leitura de Career State; drafts de currículo, follow-up e entrevista; criação de tarefa
local; arquivamento reversível de evidência. IDs proibidos incluem submit, send email, login,
CAPTCHA, sessão, pagamento e delete profile.

