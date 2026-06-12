# Compliance, ética e limites de automação

## Objetivo

Este documento define limites para que o SotuHire seja um projeto profissional, apresentável e seguro.

Ferramentas de vagas podem facilmente virar spam bots. O SotuHire deve seguir outro caminho:

> Assistir o candidato, não substituir sua responsabilidade.

## Princípio central

O SotuHire deve:

- ajudar a decidir;
- explicar recomendações;
- preparar textos;
- organizar oportunidades;
- preservar revisão humana;
- respeitar privacidade;
- respeitar limites de plataformas.

O SotuHire não deve:

- aplicar em massa;
- simular usuário para burlar regras;
- extrair dados privados;
- enviar mensagens sem revisão;
- contornar bloqueios técnicos;
- esconder origem dos dados.

## Scraping responsável

Scraping deve ser usado apenas quando fizer sentido e respeitar limites.

### Permitido

- páginas públicas;
- HTML acessível sem login;
- APIs oficiais;
- feeds públicos;
- textos colados pelo usuário;
- links salvos manualmente;
- newsletters públicas;
- páginas de carreira de empresas.

### Não permitido no projeto

- bypass de CAPTCHA;
- bypass de autenticação;
- uso de cookies roubados ou compartilhados;
- coleta de dados pessoais em massa;
- scraping de áreas privadas;
- proxies para contornar bloqueio;
- automação de candidatura em massa;
- spam para recrutadores;
- automação que gere engajamento falso.

## LinkedIn

O LinkedIn deve ser tratado como fonte manual/assistiva.

Motivo: o contrato de usuário do LinkedIn restringe scripts, robôs, crawlers, plugins e outros meios para copiar/raspar serviços, perfis e dados; também restringe bots e métodos automatizados não autorizados para acessar serviços, adicionar/baixar contatos, enviar mensagens ou gerar engajamento.

No SotuHire, o uso seguro é:

- usuário copia a descrição;
- usuário copia o texto do post;
- usuário salva o link manualmente;
- usuário revisa qualquer mensagem gerada;
- nenhuma aplicação automática é feita.

## Geração de conteúdo com IA

Mensagens para recrutadores, respostas de formulário e cartas devem ser tratadas como rascunhos.

Sempre deixar claro:

- o usuário deve revisar;
- o usuário deve corrigir dados;
- o usuário deve remover exageros;
- o usuário é responsável pelo que envia.

## Dados pessoais

O SotuHire lida com currículo. Portanto, deve minimizar dados.

Boas práticas:

- salvar localmente por padrão;
- não enviar currículo para serviços externos sem aviso;
- permitir apagar histórico;
- não salvar API keys em código;
- não versionar currículos reais;
- usar exemplos fictícios nos testes.

## Logs

Logs não devem expor:

- currículo completo;
- e-mail pessoal;
- telefone;
- documentos;
- links privados;
- tokens;
- API keys.

Logs devem focar em:

- fonte;
- status;
- erro técnico;
- tempo;
- quantidade de itens.

## Política de auto-apply

Auto-apply em massa fica fora do escopo.

Motivos:

- risco de spam;
- risco de candidatura errada;
- risco de violar termos de plataformas;
- baixa qualidade para recrutadores;
- risco para conta do usuário;
- pior valor de portfólio.

O SotuHire pode preparar:

- mensagem;
- carta;
- resposta;
- checklist;
- ajustes no currículo;
- link da vaga.

Mas a ação final deve ser humana.

## Extensão de navegador

Uma extensão futura deve ser assistiva:

Permitido:

- ler o texto da vaga aberta pelo usuário;
- enviar o texto ao SotuHire local;
- mostrar match;
- salvar no tracker;
- gerar rascunho.

Não permitido:

- coletar feed em massa;
- navegar sozinho por páginas;
- aplicar automaticamente;
- enviar mensagens;
- burlar limitações.

## Checklist antes de criar um conector

Antes de implementar uma fonte, responder:

1. A página é pública?
2. Existe API oficial?
3. Existe feed?
4. A fonte permite esse uso?
5. O dado é realmente necessário?
6. Há dados pessoais?
7. O scraper respeita `robots.txt`?
8. Existe rate limit?
9. Existe cache?
10. O usuário consegue revisar a oportunidade?
11. A fonte pode ser desativada facilmente?
12. Há teste com fixture?

## Conclusão

O SotuHire pode usar scraping, mas deve usar scraping como engenharia de coleta de dados, não como gambiarra para burlar plataformas.

A postura correta é:

```text
coletar oportunidades públicas
normalizar dados
explicar match
preparar candidatura
manter decisão humana
```
