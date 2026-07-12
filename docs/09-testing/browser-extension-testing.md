# Testes da extensão assistiva

## Cobertura automatizada

- Manifest V3 válido e permissões mínimas;
- payload Pydantic compatível com o content script;
- Local API restrita a localhost;
- payload acima do limite rejeitado;
- captura vira oportunidade e memória;
- captura pode ser analisada e enviada ao tracker;
- `collection_method` e fontes persistem;
- repetição não duplica captura, cartão ou memória;
- a mesma vaga em portais diferentes é consolidada;
- lote paginado diferencia itens novos e existentes;
- API não expõe chave Gemini.
- repositório público vira relatório tipado com fallback local;
- arquivos centrais são priorizados e artefatos grandes/gerados são ignorados;
- commits e README são analisados;
- modos standalone e conectado permanecem separados;
- chaves Gemini/OpenAI ficam fora do content script e do payload conectado;
- storage de sessão é o padrão e persistência local exige consentimento;
- catálogo oficial e modelo selecionado são exercitados no harness do service worker;
- falha do provider preserva fallback local e trace explícito;
- botão injetado cobre repositório, `tree`, `blob` e perfil público;
- modal contém score, estados e ações obrigatórias;
- pacote da Chrome Web Store contém somente runtime e não contém segredos.

As fixtures em `tests/fixtures/extension/` são inteiramente fictícias e não dependem de portais
reais.

## Validação manual

1. Rode `streamlit run app.py`.
2. Inicie a API pela aba **Extensão**.
3. Carregue `browser-extension/` como extensão sem compactação.
4. Abra uma página fictícia/local e teste conexão, captura, análise e tracker.
5. Reenvie a mesma página e confirme que os totais não aumentam.
6. Acumule duas páginas no lote e confirme o resumo de novas/duplicadas.
7. Capture a mesma vaga em dois domínios e confirme um cartão com duas fontes.

## JavaScript

Valide a sintaxe sem executar rede:

```bash
node --check browser-extension/popup.js
node --check browser-extension/background.js
node --check browser-extension/content.js
node --check browser-extension/project_analysis.js
node --check browser-extension/github_injected.js
python scripts/package_extension.py
```
