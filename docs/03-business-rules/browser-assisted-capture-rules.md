# Regras de captura assistida pelo navegador

## Escopo

A extensão processa a página que a pessoa abriu manualmente. Ela lê conteúdo visível somente após
uma ação explícita, sem receber credenciais e sem automatizar login.

O contrato é multiportal. A extração de vaga prioriza:

1. JSON-LD `schema.org/JobPosting`;
2. seletores semânticos de título, empresa e localização;
3. texto visível da área principal ou da página.

JSON-LD inválido não interrompe a captura: o fallback semântico continua disponível. O payload
registra `extraction_strategy` e preserva `structured_data` quando existe.

## Ações permitidas

- salvar e analisar a vaga atual;
- enviar a vaga ao Tracker;
- copiar o texto visível;
- capturar um edital/concurso público para revisão;
- importar candidaturas já realizadas que estejam visíveis;
- acumular páginas revisadas manualmente em um lote;
- analisar GitHub/portfólio localmente;
- usar a IA configurada no SotuHire local;
- usar Gemini/OpenAI próprios após configuração explícita;
- gerar candidatos revisáveis para o Perfil Universal.

## Identidade e proveniência

- a mesma URL com parâmetros de tracking diferentes representa a mesma pendência/captura;
- URL normalizada tem precedência sobre um `capture_id` transitório na fila;
- a identidade é recalculada ao importar uma fila;
- empresa igual e título fortemente semelhante podem sugerir consolidação entre portais;
- uma consolidação preserva URLs, domínios e referências de origem;
- conteúdo semelhante de organizações diferentes não deve ser mesclado automaticamente;
- `source`, `source_ref`, método de coleta e hash acompanham snapshots e candidatos.

## Fila offline

Uma falha de conexão não descarta a ação. A fila local registra:

```txt
identity
path
body
queued_at
retry_count
last_error
next_retry_at
state
max_attempts
```

O retry usa backoff exponencial a partir de 30 segundos e no máximo cinco tentativas por item. Ao
atingir o limite, a pendência permanece como `failed` para revisão, nova captura ou exportação.

O export remove campos cujos nomes indicam API key, autorização, token, cookie, senha, segredo ou
credencial. Valores com formato de chave Gemini/OpenAI são redigidos. O import aceita até 500 itens
sob `/capture/`, sanitiza novamente e não confia na identidade fornecida pelo arquivo.

## Snapshots

- uma vaga conectada cria `JobSnapshot`;
- um edital cria `PublicExamSnapshot`;
- uma análise pode criar `ResumeSnapshot` e `AnalysisSnapshot`;
- o Tracker referencia os snapshots realmente usados;
- snapshots são imutáveis e deduplicados por hash de conteúdo;
- mudar a página de origem não altera versões anteriores.

## IA e chaves

- a chave do app nunca sai do backend local;
- chave própria Gemini/OpenAI fica em `chrome.storage.session` por padrão;
- persistência em IndexedDB exige consentimento explícito;
- IndexedDB não deve ser descrito como criptografia;
- a extensão nunca usa `chrome.storage.sync` para segredo;
- content script, página, Companion, logs, fila, export e screenshots não recebem a chave;
- o modelo escolhido deve ser enviado à chamada real;
- falha de provider deve preservar fallback local com motivo explícito;
- resultado de IA exige revisão e não comprova experiência ou habilidade por si só.

## Limites obrigatórios

- nenhum login, senha ou autenticação automática;
- nenhum CAPTCHA/checkpoint bypass;
- nenhum cookie, token, sessão, header autenticado ou storage de terceiros;
- nenhum auto-apply, inscrição, pagamento, boleto ou envio de documentos;
- nenhum clique automático em botão nativo de candidatura;
- nenhum scraping em massa ou monitoramento da navegação;
- lote de candidaturas limitado a 500 itens;
- captura e envio continuam ações explícitas.

O authenticated-browser não faz parte desta extensão e permanece isolado.

## Dados e remoção

Preferências, lote e fila ficam no storage local da extensão. Chave temporária usa storage de
sessão; persistência consentida usa IndexedDB do service worker. Capturas e snapshots conectados
ficam nos stores locais do SotuHire.

O backup do app não inclui storage/IndexedDB do navegador. A fila possui export separado e
sanitizado. Remover a extensão não remove capturas já importadas; elas devem ser gerenciadas no
SotuHire local.
