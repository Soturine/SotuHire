# Política de Privacidade da Extensão SotuHire

A extensão processa conteúdo visível da aba após ação explícita da pessoa usuária. Em páginas
públicas do GitHub, ela injeta o botão **SotuHire AI** para analisar sinais públicos do perfil ou
repositório.

A extensão não captura cookies, senhas, tokens, `localStorage`, `sessionStorage`, headers
autenticados ou dados privados ocultos. Não automatiza login, CAPTCHA ou candidatura.

Os dados podem permanecer no navegador, ser enviados à Local Companion API em
`http://127.0.0.1:8765` ou, mediante configuração explícita, ao Gemini/OpenAI usando a chave da
própria pessoa usuária. A chave é usada somente pelo service worker: fica em
`chrome.storage.session` por padrão ou em um cofre IndexedDB privado após consentimento explícito.
Nunca usa `chrome.storage.sync`, nunca é injetada na página e nunca é enviada ao SotuHire.

Para análise avançada, a extensão pode consultar metadados públicos, README, commits, linguagens,
topics e estrutura pela API pública do GitHub, sem token, cookies ou credenciais. O conteúdo só é
enviado ao provider escolhido quando a pessoa inicia a análise.

O SotuHire é local-first. A pessoa usuária controla quando capturar, analisar, salvar ou remover
seus dados locais.
