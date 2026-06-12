# Estratégia de Provedores de IA

O SotuHire deve começar simples, mas nascer preparado para trocar de provedor de IA sem reescrever regra de negócio.

## Objetivo

Separar:

```text
regra de negócio != prompt != provedor de IA != interface
```

O módulo de análise deve depender de uma interface `AIProvider`, não diretamente de Gemini, OpenAI ou outro serviço.

## Providers planejados

| Provider | Uso | Momento |
|---|---|---|
| Gemini | MVP inicial e structured output | v0.1/v0.2 |
| OpenAI | alternativa para modelos robustos | futuro |
| OpenRouter | escolha de múltiplos modelos por API compatível | futuro |
| Ollama | modo local/offline e privacidade | futuro |

Links:

- [Gemini API](https://ai.google.dev/)
- [OpenAI API](https://platform.openai.com/docs)
- [OpenRouter](https://openrouter.ai/docs/quickstart)
- [Ollama](https://ollama.com/)

## Interface proposta

```python
class AIProvider:
    def generate_json(self, prompt: str, schema: dict) -> dict:
        """Generate a JSON-compatible response according to a schema."""
        raise NotImplementedError
```

## Regras

- Toda resposta crítica deve ser JSON estruturado.
- O prompt deve pedir evidências e não apenas opinião.
- O schema deve validar score, gaps, pontos fortes e recomendação.
- O provider não deve conhecer UI.
- O provider não deve salvar dados sem autorização.
- O provider deve receber apenas contexto necessário.

## Relação com RAG

O RAG monta contexto. O provider apenas gera saída.

```mermaid
flowchart LR
    A[Retriever] --> B[Context Builder]
    B --> C[AIProvider]
    C --> D[JSON Schema Validation]
    D --> E[Report]
```

## OpenRouter

OpenRouter pode ser útil porque permite alternar modelos mantendo uma API parecida com OpenAI. Isso ajuda quando:

- um modelo fica caro;
- um modelo fica indisponível;
- um modelo é melhor para português;
- o usuário quer escolher custo/qualidade;
- o projeto quer comparar respostas.

## Ollama/local

Ollama pode ser útil para:

- privacidade;
- testes locais;
- reduzir custo;
- demos offline;
- análise de documentos menos sensíveis.

Limitação: modelos locais podem ser mais fracos, lentos ou exigir máquina melhor.

## Decisão de arquitetura

No MVP, usar um provider simples. Na arquitetura, deixar interface pronta.

```text
Não implementar múltiplos providers antes do MVP.
Mas não acoplar o código a um provider só.
```
