# Segurança e privacidade

## Por que importa

Currículo contém dados pessoais: nome, e-mail, telefone, cidade, histórico acadêmico e profissional. O SotuHire deve tratar esse conteúdo com cuidado desde o MVP.

## Dados sensíveis

Podem aparecer em currículos:

- nome completo;
- e-mail;
- telefone;
- endereço;
- LinkedIn;
- GitHub;
- histórico de trabalho;
- formação;
- projetos;
- certificações.

## Regras para o repositório

Nunca commitar:

- currículo real;
- `.env`;
- chave de API;
- resposta de IA com dados pessoais;
- banco SQLite real com candidaturas;
- prints com dados pessoais.

## `.gitignore` recomendado

```text
.env
*.pdf
*.docx
/data/resumes/
/data/private/
/outputs/private/
*.sqlite3
*.db
```

## Chaves de API

Use variável de ambiente:

```text
GEMINI_API_KEY=...
```

Ou `st.secrets` no Streamlit Cloud. Referência: [Streamlit Secrets Management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)

## Logs

Logs não devem imprimir currículo inteiro. Prefira:

```text
PDF recebido: 124 KB
Texto extraído: 3580 caracteres
```

Evite:

```text
Texto completo do currículo: ...
```

## Extensão e Local Companion

A extensão assistiva usa permissões mínimas (`activeTab`, `scripting` e `storage`) e hosts
restritos a localhost, GitHub público e aos providers opcionais. Ela processa a página que a pessoa
abriu e somente após uma ação explícita.

Regras para segredos da extensão:

- a chave configurada no SotuHire permanece no backend local e nunca chega ao navegador;
- uma chave própria Gemini/OpenAI fica em `chrome.storage.session` por padrão;
- persistência exige consentimento e usa IndexedDB acessível pelo service worker;
- IndexedDB não deve ser descrito como criptografia adicional;
- nenhuma chave usa `chrome.storage.sync`, content script, página aberta ou payload conectado;
- o botão **Remover chave** limpa sessão, IndexedDB e resíduos do formato antigo;
- fila offline, exportação, screenshots, logs e ZIP não podem incluir chaves ou tokens;
- o token opcional do Companion é separado da chave de IA e também não pode ser exportado.

O handshake troca apenas versões, capabilities e warnings. O contexto enviado à extensão é um
resumo curto com evidências confirmadas; Perfil completo, memória completa, cookies, tokens,
headers autenticados e storage de terceiros ficam fora da ponte.

A extensão não faz login, auto-apply, inscrição, pagamento, envio de documentos, bypass de CAPTCHA
ou scraping em massa. O fluxo `authenticated-browser` é separado e não compartilha sessão com a
extensão assistiva.

## Backup, restore e exportação

O backup de dados do SotuHire pode incluir banco SQLite, stores locais necessários, configurações
não secretas, manifesto e checksums. Ele exclui por desenho:

- diretórios e arquivos de segredos;
- chaves de provider e tokens;
- cookies e dados de sessão;
- `chrome.storage` e IndexedDB da extensão;
- fila do navegador, exceto quando a própria pessoa gera seu export sanitizado separado.

Antes de restaurar, o app valida manifesto, checksums e versão do schema e cria um backup preventivo
do destino. O restore não deve sobrescrever ou importar estado do navegador. A fila offline possui
export/import próprio, remove campos nomeados como credencial, redige valores com formato de chave
Gemini/OpenAI e recalcula identidades ao importar.

Snapshots de vaga, currículo, análise e edital preservam o conteúdo usado em cada decisão. Eles não
devem conter segredos, e sua imutabilidade não substitui os controles de acesso e remoção dos dados
locais.

## Retenção

No MVP, o mais seguro é não salvar currículo automaticamente. Se salvar no futuro:

- avisar o usuário;
- permitir deletar;
- separar dados privados;
- não versionar;
- considerar criptografia se virar produto real.

## IA externa

Ao usar APIs de IA, lembre que o currículo será enviado para um serviço externo. A documentação deve deixar isso claro.

### Traces e feedback

`AiRunStore` persiste somente metadados mínimos, hashes, contagens e referências seguras. Inputs/outputs integrais ficam desativados por padrão; erros são sanitizados e a retenção é configurável. Feedback humano guarda o vínculo com `run_id`, a avaliação e um comentário opcional sanitizado, nunca a resposta original.

Conteúdo importado é delimitado como não confiável. Prompt injection não pode solicitar chave, revelar system prompt, promover afirmação sem evidência ou alterar uma decisão determinística. Benchmarks externos usam apenas fixtures fictícias e variáveis temporárias; chaves não entram em frontend, SQLite, logs, screenshots ou pacote da extensão.

## Mensagens geradas

O usuário deve revisar toda mensagem antes de enviar. A IA pode cometer erro, exagerar ou omitir informações.
