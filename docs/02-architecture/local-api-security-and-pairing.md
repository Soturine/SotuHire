# Segurança e pairing das APIs locais

## Fronteira protegida

As APIs de frontend (porta 8787) e Companion (porta 8765) escutam exclusivamente em loopback.
`localhost` não é tratado como confiança: antes de executar uma rota, a fronteira valida o
cliente de socket, `Host`, `Origin`, método, autenticação, `Content-Type`, tamanho do corpo,
profundidade do JSON, tamanho de lote, rate limit e timeout.

O health check é público e contém apenas versão/capabilities. OpenAPI e documentação podem ser
lidos sem sessão; dados e operações exigem autenticação. Uma requisição sem `Origin` é aceita
como cliente nativo somente com token de instalação. Uma requisição com `Origin` desconhecida é
rejeitada mesmo que tente apresentar credenciais.

As origins padrão são apenas portas locais conhecidas. Uma origin remota requer
`SOTUHIRE_API_ALLOW_REMOTE_ORIGINS=1` e produz warning explícito. A API não aceita bind público;
modo de desenvolvimento não desativa essa regra.

## Credenciais e lifecycle

O backend gera um token aleatório por instalação somente quando ele é necessário. O arquivo
local é criado atomicamente em `data/security/local-auth.json`, com permissão restritiva quando
o sistema operacional oferece suporte. O valor nunca aparece em health, exceções, logs, URL,
bundle Vite ou respostas de pairing. Backup e exportação já excluem arquivos que contêm material
classificado como token/credencial.

Clientes nativos podem fornecer o token no header `X-SotuHire-Token`. Navegadores não recebem
esse token:

1. o frontend solicita uma prova aleatória curta a partir de uma origin local autorizada;
2. a prova fica em memória e é trocada uma única vez;
3. o backend emite cookie `HttpOnly`, `SameSite=Strict`, limitado a `/api`;
4. o CSRF associado fica apenas na memória do frontend e acompanha operações mutáveis;
5. expiração, origin diferente, CSRF ausente ou replay invalidam a operação.

Recarregar a página pode exigir novo pairing para recuperar o CSRF; reiniciar a API encerra as
sessões em memória. Essa perda é intencional e não apaga dados do usuário.

## Extensão MV3

O popup e os content scripts nunca leem credencial do Companion. A ação explícita “Parear
extensão nesta sessão” pede ao service worker uma prova ligada à origin
`chrome-extension://...`, consome-a uma vez e guarda o token de sessão em
`chrome.storage.session`. Não há `chrome.storage.sync`, `localStorage`, `sessionStorage` nem
`chrome.storage.local` para esse token. Todas as chamadas conectadas passam pelo service worker;
quando a sessão expira, a fila offline continua preservada e a UI solicita novo pairing.

Chaves opcionais de providers externos seguem contrato separado: sessão por padrão e
persistência local somente após opt-in explícito. Elas nunca são enviadas ao Companion nem a
content scripts.

## Limites e resposta a abuso

- corpo geral da API: até 12 MiB; Companion: até 1 MiB;
- lotes: até 100 itens por requisição;
- JSON: até 16 níveis, inspecionado iterativamente;
- rate limit local: janela deslizante de 120 requisições por minuto por cliente e rota;
- timeout: 30 segundos;
- JSON, multipart e octet-stream são aceitos pela API conforme o contrato de rota; Companion
  aceita JSON em POST;
- erros usam mensagens fixas, `Cache-Control: no-store` e não refletem corpo, proof ou token.

## Recuperação e diagnóstico

Se o arquivo de autenticação estiver inválido, a API falha explicitamente em vez de criar uma
nova identidade silenciosa. O operador deve preservar o arquivo para diagnóstico, removê-lo
manualmente somente se quiser revogar todos os clientes e então reiniciar. Um novo token não
altera o banco SQLite, snapshots, perfil ou candidaturas; apenas exige novo pairing.

Os testes cobrem origin permitida/negada/ausente, Host, token válido/inválido/ausente, cookie,
CSRF, expiração, replay, body oversized, lote, profundidade, Content-Type, OPTIONS, health,
frontend e extensão. Nenhum screenshot de release deve mostrar proofs, CSRF ou tokens.
