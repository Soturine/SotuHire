# Política de Privacidade da Extensão SotuHire

A extensão processa conteúdo visível da aba somente após uma ação explícita. Em páginas públicas do
GitHub, ela pode mostrar o botão **SotuHire Insight** para analisar sinais públicos de perfil ou
repositório.

## Dados processados

Conforme a ação escolhida, a extensão pode processar:

- título, empresa, localização, descrição, URL e JSON-LD de uma vaga;
- texto visível de um edital ou lista de candidaturas já realizadas;
- README, commits, linguagens, topics, arquivos e metadados públicos do GitHub;
- preferências do popup, lote e fila offline.

A extensão não captura cookies, senhas, tokens, sessão, `localStorage`, `sessionStorage`, headers
autenticados ou dados privados ocultos. Não automatiza login, CAPTCHA, candidatura, inscrição,
pagamento, mensagem ou envio de documentos.

## Integração local

Dados escolhidos podem ser enviados à Local Companion API em `http://127.0.0.1:8765` ou à API local
do SotuHire em `http://127.0.0.1:8787`. A integração cria capturas e snapshots locais revisáveis.
O site não precisa estar aberto para a Companion receber uma ação.

Se a conexão falhar, a ação pode permanecer em uma fila local com retry. O export da fila remove
campos nomeados como credencial e redige valores com formato de chave Gemini/OpenAI. O backup geral
do SotuHire não inclui storage nem IndexedDB do navegador.

## Inteligência artificial

A pessoa pode usar:

- análise local sem chave;
- IA configurada no SotuHire, cuja chave permanece no backend;
- Gemini ou OpenAI com chave própria da extensão.

Uma chave própria é usada somente pelo service worker. Por padrão, fica em
`chrome.storage.session`. A persistência opcional usa IndexedDB local após consentimento explícito;
isso não representa uma promessa de criptografia adicional. A extensão nunca usa
`chrome.storage.sync` para segredo, nunca injeta a chave na página e nunca a envia ao SotuHire.

O conteúdo público só é enviado ao provider selecionado quando a pessoa inicia a análise. O modelo
escolhido é usado na chamada real. Falhas preservam o fallback local e são identificadas no
relatório.

## GitHub público

Para análise avançada, a extensão pode consultar metadados, README, commits, linguagens, topics e
estrutura pela API pública do GitHub, sem token, cookies ou credenciais. Rate limits e falhas não
ampliam permissões nem autorizam coleta privada.

## Controle da pessoa usuária

A pessoa controla quando capturar, analisar, salvar, exportar ou remover dados. **Remover chave**
limpa a sessão e a persistência consentida. Desinstalar a extensão remove seu estado do navegador,
mas não apaga capturas já importadas no SotuHire local.
