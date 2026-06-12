# Ruff no SotuHire

## Objetivo

O SotuHire usa Ruff para manter qualidade e consistência no código Python.

Ruff é um linter e formatador Python rápido, escrito em Rust. Ele pode substituir várias ferramentas separadas em projetos pequenos e médios, como parte de Flake8, isort, Black, pyupgrade e plugins comuns.

## Por que usar Ruff

Para o SotuHire, Ruff faz sentido porque:

- é rápido;
- reduz ferramentas no projeto;
- funciona bem com `pyproject.toml`;
- roda fácil no terminal;
- integra bem com CI;
- ajuda a manter Clean Code;
- evita commits com imports quebrados, variáveis não usadas e formatação inconsistente.

## Comandos principais

Verificar problemas:

```bash
ruff check .
```

Corrigir automaticamente quando possível:

```bash
ruff check . --fix
```

Formatar:

```bash
ruff format .
```

Verificar se está formatado sem alterar arquivos:

```bash
ruff format . --check
```

## Configuração recomendada

O arquivo `pyproject.toml` deve centralizar a configuração:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"
src = ["modules", "tests"]

[tool.ruff.lint]
select = [
  "E",
  "F",
  "I",
  "B",
  "UP",
  "SIM",
]
ignore = [
  "E501"
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
```

## Regras iniciais

Para não virar overengineering, comece com regras úteis:

- `E`: pycodestyle;
- `F`: Pyflakes;
- `I`: organização de imports;
- `B`: flake8-bugbear;
- `UP`: pyupgrade;
- `SIM`: simplificações.

Evite ativar regras demais logo no começo. O foco é melhorar o código, não travar desenvolvimento.

## Integração com pytest

O fluxo local deve ser:

```bash
ruff check .
ruff format . --check
pytest
```

## Integração com GitHub Actions

O CI deve rodar:

```bash
python -m ruff check .
python -m ruff format . --check
python -m pytest
```

## Quando usar `--fix`

Pode usar:

```bash
ruff check . --fix
```

Antes de commitar, revise o diff:

```bash
git diff
```

Não aceite correções automáticas cegamente em regra de negócio.

## O que não colocar no Ruff

Ruff não substitui:

- testes;
- validação de schema;
- revisão humana;
- análise de arquitetura;
- documentação;
- segurança;
- bom senso.

Ele é uma camada de qualidade, não a qualidade inteira.
