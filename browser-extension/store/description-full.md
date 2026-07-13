# SotuHire Assistive Browser Companion

Leve vagas, candidaturas e evidências técnicas para o copiloto de carreira local-first SotuHire.

Em perfis e repositórios públicos do GitHub, o botão **SotuHire Insight** abre um relatório visual com nota,
grade, stack, qualidade do README, commits, arquitetura, prontidão para recrutadores e evidências
úteis para currículo. O relatório pode funcionar localmente no navegador, usar a IA configurada
no SotuHire ou usar uma chave opcional Gemini/OpenAI isolada no service worker. O catálogo oficial
é atualizável e o modelo selecionado é aplicado de verdade à análise.

A chave própria usa sessão por padrão; persistência local em IndexedDB ocorre somente após
consentimento e pode ser removida no popup. A extensão nunca usa `chrome.storage.sync` para
segredos.

O popup também captura vagas abertas manualmente, envia para análise ou tracker e importa páginas
visíveis de candidaturas sem duplicar registros já conhecidos. JSON-LD `JobPosting` tem prioridade,
e o modo conectado preserva snapshots. Se a Companion estiver offline, a fila registra retry e pode
ser exportada/importada sem credenciais.

Privacidade por padrão: sem cookies, tokens, senhas, headers autenticados, armazenamento da página
ou automação de login.
