# Regras de filtragem de vagas

## Objetivo

Filtrar vagas ruins cedo economiza tempo e custo de IA. Se uma vaga é claramente incompatível, o sistema pode marcar como baixa aderência antes de gastar processamento detalhado.

## Termos de prioridade

Termos que indicam oportunidade mais alinhada ao perfil inicial:

```text
estágio
estagiário
intern
trainee
júnior
junior
assistente
sem experiência
primeira oportunidade
dados
analytics
python
sql
excel
qa
testes
suporte técnico
automação
ia
inteligência artificial
machine learning
api
```

## Termos de atenção

Termos que exigem cuidado:

```text
pleno
experiência prévia obrigatória
inglês avançado
superior completo
certificação obrigatória
plantão
PJ obrigatório
presencial obrigatório
```

## Termos de desclassificação ou forte redução

```text
sênior
senior
especialista
tech lead
arquiteto
principal engineer
staff engineer
5+ anos
7+ anos
10+ anos
terraform obrigatório
aws avançado obrigatório
kubernetes avançado obrigatório
liderança técnica obrigatória
```

## Regras por modalidade

O usuário pode configurar preferências:

- remoto;
- híbrido em São Paulo;
- híbrido em São José dos Campos;
- presencial em Jacareí/SJC/Vale do Paraíba;
- aceitar mudança ou não.

Vagas fora da preferência não precisam ser descartadas automaticamente, mas devem receber alerta.

## Regras por área

Áreas prioritárias iniciais:

- Estágio em IA;
- Estágio em Dados;
- Estágio em Automação;
- Suporte Técnico;
- QA Jr;
- Desenvolvedor Jr;
- Analista de Dados Jr;
- Assistente de Projetos de TI.

## Classificação final

O sistema pode combinar:

- score da IA;
- flags determinísticas;
- senioridade;
- modalidade;
- palavras-chave.

Exemplo:

```text
Score IA: 78
Flag: "sênior" detectada
Experiência obrigatória: 5+ anos
Score final ajustado: 38
Recomendação: Não aplicar
```

## Explicação obrigatória

Toda filtragem deve ser explicada. Não basta esconder a vaga.

Exemplo:

> Marcada como baixa aderência porque a descrição exige perfil sênior, liderança técnica e mais de 5 anos de experiência.
