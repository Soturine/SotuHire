# ML avançado futuro: PyTorch, embeddings e agentes

Este documento registra ideias futuras. **PyTorch, fine-tuning, classificadores próprios e agentes avançados não fazem parte do MVP atual.**

## Decisão atual

O SotuHire deve manter o MVP leve:

- Python;
- Streamlit;
- Pydantic;
- Gemini/OpenAI opcional;
- SQLite;
- Ruff;
- pytest.

Não adicionar agora:

- PyTorch obrigatório;
- fine-tuning;
- modelo próprio;
- agent framework complexo;
- multi-agent pesado.

## O que pode entrar no futuro

Quando o produto tiver histórico real, pode fazer sentido adicionar:

- embeddings locais;
- reranking de vagas;
- classificador de post real vs ruído;
- detector de senioridade;
- avaliação semântica de portfólio;
- memória vetorial mais forte.

## RAG simples agora, ML pesado depois

O RAG inicial pode ser simples:

```text
texto -> chunks -> busca lexical/semântica simples -> evidências -> análise estruturada
```

Depois, se necessário:

```text
sentence-transformers / ChromaDB / FAISS / PyTorch
```

## Agentes como inspiração

A ideia de agentes especializados é útil, mas deve começar como funções e classes simples:

- `ResumeAgent` vira módulo de currículo;
- `JobAgent` vira parser de vaga;
- `MatchAgent` vira analyzer;
- `ComplianceAgent` vira regras e guardrails.

O nome “Hermes” fica apenas como inspiração conceitual de memória, verificação e orquestração. Não deve ser dependência nem framework agora.
