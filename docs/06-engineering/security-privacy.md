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

## Retenção

No MVP, o mais seguro é não salvar currículo automaticamente. Se salvar no futuro:

- avisar o usuário;
- permitir deletar;
- separar dados privados;
- não versionar;
- considerar criptografia se virar produto real.

## IA externa

Ao usar APIs de IA, lembre que o currículo será enviado para um serviço externo. A documentação deve deixar isso claro.

## Mensagens geradas

O usuário deve revisar toda mensagem antes de enviar. A IA pode cometer erro, exagerar ou omitir informações.
