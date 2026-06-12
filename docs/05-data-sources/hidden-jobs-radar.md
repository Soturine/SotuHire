# Hidden Jobs Radar

## O que é

O **Hidden Jobs Radar** é o módulo futuro do SotuHire que identifica oportunidades em textos informais. Muitas vagas boas não aparecem como anúncio formal. Elas surgem como posts, indicações, comentários ou mensagens de recrutadores.

Exemplos:

```text
Estamos contratando estagiário de dados. Quem tiver indicação, me chama.
```

```text
Vaga remota para QA Jr. Enviar currículo para o e-mail abaixo.
```

```text
Meu time abriu posição para automação com Python. Aceitamos candidatos júnior.
```

## Objetivo

Transformar texto informal em dados estruturados:

```json
{
  "is_job_post": true,
  "job_title": "QA Jr",
  "company": "Não informada",
  "location": "Remoto",
  "contact": "email encontrado",
  "requirements": ["QA", "testes", "júnior"],
  "confidence": 0.86
}
```

## Sinais de oportunidade

Palavras e expressões úteis:

```text
vaga
oportunidade
estamos contratando
contratando
recrutando
indicação
me chama no inbox
envie currículo
currículo para
processo seletivo
time aberto
posição aberta
estágio
júnior
remoto
híbrido
```

## Tipos de post

| Tipo | Exemplo | Ação |
|---|---|---|
| Vaga direta | “Vaga para Estágio em Dados” | Extrair dados e calcular match |
| Indicação | “Tenho indicação para QA Jr” | Gerar mensagem de abordagem |
| Banco de talentos | “Cadastre-se no nosso banco” | Marcar como oportunidade fraca/média |
| Post genérico | “Estamos crescendo” | Classificar como incerto |
| Não vaga | “Dicas para entrevista” | Ignorar ou salvar como conteúdo |

## Uso de IA

A IA é útil porque posts informais são ambíguos. Ela pode classificar:

- se é vaga real;
- qual é o cargo;
- qual é a empresa;
- se é remoto/híbrido/presencial;
- qual é o contato;
- quais requisitos aparecem;
- qual o nível de confiança.

## Limites

O radar não deve:

- invadir plataformas;
- acessar conta sem autorização;
- coletar dados privados;
- enviar mensagem automática em massa;
- fingir ser humano;
- burlar limites técnicos.

## Fluxo seguro

1. Usuário cola post ou link.
2. Sistema analisa o texto fornecido.
3. Sistema classifica se é oportunidade.
4. Sistema extrai dados.
5. Sistema calcula match.
6. Sistema gera mensagem de abordagem.
7. Usuário revisa e decide.

## Diferencial para portfólio

Esse módulo mostra conhecimento em:

- NLP;
- classificação de texto;
- extração de entidades;
- estruturação de dados;
- IA generativa;
- regras de negócio;
- produto real.
