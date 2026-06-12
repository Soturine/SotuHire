# Roadmap da Extensão Assistiva

A extensão do SotuHire deve ser assistiva, não agressiva.

Ela deve funcionar como ponte entre a página aberta e o app local/web do SotuHire.

## Objetivo

Adicionar botões úteis no navegador:

- Analisar vaga com meu currículo;
- Salvar vaga no tracker;
- Analisar post como oportunidade;
- Analisar repositório como portfólio;
- Gerar mensagem para recrutador;
- Enviar texto para o SotuHire local.

## Não objetivos

- Não aplicar automaticamente.
- Não enviar mensagem automaticamente.
- Não raspar feed logado em massa.
- Não coletar dados sem clique explícito.
- Não monitorar navegação inteira.

## Arquitetura

```mermaid
flowchart LR
    A[Content Script] --> B[Extrai texto visível]
    B --> C[Popup da extensão]
    C --> D[Usuário confirma]
    D --> E[SotuHire API local]
    E --> F[Análise]
    F --> G[Tracker]
```

## APIs úteis

- [Chrome Extensions](https://developer.chrome.com/docs/extensions/)
- [chrome.storage](https://developer.chrome.com/docs/extensions/reference/api/storage)
- [Chrome Messaging](https://developer.chrome.com/docs/extensions/develop/concepts/messaging)

## Escopo por fase

### Fase 1

- popup simples;
- campo para URL do app local;
- botão copiar texto da página;
- botão enviar para análise.

### Fase 2

- detectar páginas de vaga;
- extrair título, empresa, descrição e link;
- salvar no tracker.

### Fase 3

- detectar posts de oportunidade;
- classificar texto informal;
- gerar mensagem.

### Fase 4

- analisar GitHub/portfólio;
- cache por URL/commit;
- exibir Portfolio Score.

## Privacidade

- Mostrar ao usuário o texto que será enviado.
- Permitir cancelar.
- Não salvar cookies.
- Não pedir permissões amplas sem necessidade.
- Não enviar dados para terceiros sem configuração.

## Relação com RepoLogs

RepoLogs inspira a ideia de botão contextual e análise em página aberta. O SotuHire adapta essa ideia para carreira:

- vaga aberta;
- post aberto;
- repositório aberto;
- perfil/portfólio aberto.

Referência: [RepoLogs GitHub Extension](https://github.com/VictoriaSCorreia/RepoLogs_GithubExtension).
