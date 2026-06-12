# Guia de contribuição

## Filosofia

Contribuições devem melhorar o produto sem adicionar complexidade desnecessária. O SotuHire valoriza clareza, simplicidade, testes e documentação.

## Antes de contribuir

Leia:

- [Visão do produto](../01-product/vision.md)
- [Escopo dos MVPs](../01-product/mvp-scope.md)
- [Clean Code e SOLID](../06-engineering/clean-code-solid.md)
- [Evitando overengineering](../06-engineering/avoid-overengineering.md)

## Workflow

1. Escolha uma tarefa pequena.
2. Crie uma branch descritiva.
3. Faça mudanças focadas.
4. Adicione ou atualize testes.
5. Atualize docs quando necessário.
6. Abra PR com resumo claro.

## Padrão de branch

```text
feature/match-score
fix/pdf-empty-text
refactor/business-rules
docs/roadmap-update
test/seniority-rules
```

## Padrão de PR

A descrição do PR deve responder:

- o que foi alterado?
- por que foi alterado?
- como testar?
- há impacto em regras de negócio?
- há impacto em privacidade?

## Checklist

- [ ] Código roda localmente.
- [ ] Testes passam.
- [ ] Não há dados pessoais commitados.
- [ ] Não há chave de API.
- [ ] Regras novas estão documentadas.
- [ ] Mudança não adiciona overengineering.

## Boas práticas

- prefira funções pequenas;
- evite duplicação;
- escreva nomes claros;
- documente decisão não óbvia;
- não misture refatoração gigante com feature pequena.
