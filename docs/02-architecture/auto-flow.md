# Fluxo Automático

## Objetivo

No modo rápido, o caminho principal é:

```text
Enviar currículo -> colar vaga -> análise aparece.
```

Preferências avançadas continuam opcionais e recolhidas.

## Processamento

O upload de currículo é processado quando o conteúdo muda. Texto colado também é processado automaticamente. A vaga é analisada assim que seu texto muda.

Quando currículo e vaga existem, o modo rápido calcula uma impressão digital com:

- texto do currículo;
- texto da vaga;
- análise selecionada;
- preferências atuais.

A análise roda somente quando essa impressão digital é diferente da última execução. Isso evita loops de rerun do Streamlit.

## Botões secundários

Os botões permanecem para controle explícito:

- `Reprocessar currículo`;
- `Reprocessar vaga`;
- `Rodar análise novamente`.

Eles não são necessários para o fluxo principal.

## Exemplos

Sem conteúdo, a interface oferece:

- `Carregar exemplo de currículo`;
- `Usar vaga fictícia de exemplo`;
- `Rodar análise de exemplo`.

O fluxo completo usa somente arquivos fictícios de `examples/`.

## Limites

O modo rápido não salva automaticamente no histórico e não envia candidaturas. Revisão e confirmação de privacidade continuam obrigatórias antes de persistir uma análise.
