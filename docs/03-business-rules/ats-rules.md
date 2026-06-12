# Regras ATS

## O que é ATS neste projeto

ATS significa Applicant Tracking System, ou sistema usado por empresas para organizar e filtrar candidaturas. O SotuHire não simula perfeitamente um ATS real, mas pode verificar sinais básicos de legibilidade e estrutura.

## Objetivo da análise ATS

A análise ATS do SotuHire deve responder:

- o texto do currículo é extraível?
- existem seções claras?
- as palavras-chave da vaga aparecem?
- há riscos de formatação?
- o currículo parece fácil de ler por robôs?

## Sinais positivos

- texto extraível do PDF;
- seções com nomes claros: Experiência, Formação, Projetos, Habilidades;
- links em texto, não só ícones;
- habilidades escritas por extenso;
- datas legíveis;
- ordem lógica;
- ausência de excesso de imagens.

## Sinais negativos

- texto extraído vazio;
- currículo em imagem;
- excesso de colunas;
- tabelas complexas;
- ícones sem texto;
- informações importantes em imagem;
- seções com nomes muito criativos e pouco reconhecíveis;
- links escondidos em ícones;
- palavras-chave importantes ausentes.

## Score ATS inicial

| Score | Interpretação |
|---|---|
| 80-100 | Boa legibilidade ATS |
| 60-79 | Legível, mas pode melhorar |
| 40-59 | Risco moderado |
| 0-39 | Alto risco de leitura ruim |

## Regras determinísticas simples

Exemplo de sinais:

```python
SECTION_NAMES = [
    "experiência",
    "formação",
    "educação",
    "habilidades",
    "competências",
    "projetos",
    "certificações",
]
```

Possíveis validações:

- currículo com menos de 500 caracteres extraídos recebe alerta;
- ausência de seções conhecidas reduz score;
- ausência de e-mail/link reduz score;
- presença de palavras-chave da vaga aumenta score;
- excesso de caracteres estranhos gera alerta.


## ATS não é Currículo Lattes

O SotuHire deve separar currículo ATS de Currículo Lattes.

O Lattes é excelente para contexto acadêmico, pesquisa, iniciação científica, publicações e produção técnica, mas normalmente não é o melhor formato para uma candidatura corporativa em ATS.

Regra prática:

- use o Lattes como fonte de dados;
- extraia projetos, publicações, cursos e produção técnica relevantes;
- transforme o conteúdo em linguagem objetiva para currículo ATS;
- não envie um Lattes longo como currículo principal para toda vaga corporativa;
- para vagas de pesquisa/P&D, aumente o peso do `academic_score`.

## Limite da análise ATS

O SotuHire não deve prometer:

> Seu currículo vai passar em qualquer ATS.

Deve dizer:

> Seu currículo apresenta sinais de boa legibilidade, mas ATS reais variam por empresa e configuração.
