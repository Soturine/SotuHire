# Política de Privacidade da Extensão SotuHire

A extensão processa conteúdo visível da aba após ação explícita da pessoa usuária. Em páginas
públicas do GitHub, ela injeta o botão **SotuHire AI** para analisar sinais públicos do perfil ou
repositório.

A extensão não captura cookies, senhas, tokens, `localStorage`, `sessionStorage`, headers
autenticados ou dados privados ocultos. Não automatiza login, CAPTCHA ou candidatura.

Os dados podem permanecer no navegador, ser enviados à Local Companion API em
`http://127.0.0.1:8765` ou, mediante configuração explícita, ao Gemini usando a chave da própria
pessoa usuária. A chave Gemini standalone fica em `chrome.storage.local` e nunca é enviada ao
SotuHire.

O SotuHire é local-first. A pessoa usuária controla quando capturar, analisar, salvar ou remover
seus dados locais.
