# Clean Code e SOLID

## Objetivo

O SotuHire deve demonstrar maturidade de engenharia. Isso não significa criar arquitetura exagerada. Significa escrever código legível, modular, testável e com responsabilidades claras.

## Clean Code no projeto

### Nomes claros

Prefira:

```python
extract_text_from_pdf()
calculate_match_score()
is_senior_position()
build_recruiter_message()
```

Evite:

```python
do_stuff()
process()
handle_data()
calc()
```

### Funções pequenas

Uma função deve fazer uma coisa. Se uma função extrai PDF, chama IA, calcula score e renderiza UI, ela está grande demais.

### Sem regra escondida na UI

Errado:

```python
if "senior" in job_desc.lower():
    st.warning("Não aplicar")
```

Certo:

```python
flags = detect_seniority_flags(job_description)
st.warning(format_flags(flags))
```

### Prompts fora do app

Prompt grande dentro do `app.py` dificulta manutenção. Use `prompts.py`.

## SOLID aplicado sem exagero

### S - Single Responsibility Principle

Cada módulo deve ter uma responsabilidade principal:

- `cv_parser.py`: extrair texto;
- `ats_analyzer.py`: analisar estrutura ATS;
- `business_rules.py`: regras determinísticas;
- `ai_analyzer.py`: integração com LLM;
- `application_helper.py`: textos de candidatura.

### O - Open/Closed Principle

O código deve permitir adicionar novas fontes de vaga sem alterar todo o sistema.

Exemplo futuro:

```python
class JobSource:
    def search(self, query: str) -> list[Job]:
        raise NotImplementedError
```

Mas não precisa criar isso no MVP 1 se ainda não há buscador.

### L - Liskov Substitution Principle

Mais relevante quando houver múltiplas fontes ou provedores de IA. Um `GeminiAnalyzer` e um `OpenAIAnalyzer` devem poder ser usados pela mesma interface.

### I - Interface Segregation Principle

Não criar interfaces enormes. Um parser de currículo não precisa saber salvar banco.

### D - Dependency Inversion Principle

A UI não deve depender diretamente da API específica. Ela chama um serviço.

## O que evitar

- classes vazias só para parecer enterprise;
- abstrações antes de existir repetição;
- factories complexas no MVP;
- camadas demais;
- padrões de projeto sem necessidade.

## Boa regra prática

> Se a abstração não remove duplicação real, não simplifica teste e não facilita mudança próxima, provavelmente é overengineering.
