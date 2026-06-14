# Regras de privacidade da memória

A memória de carreira é local por padrão e controlada pela pessoa usuária.

## Regras obrigatórias

- salvar somente fatos necessários para personalização e rastreabilidade;
- não versionar `data/`, `exports/`, chaves ou currículos privados;
- permitir busca, exportação, importação e exclusão;
- permitir desativar memória por análise;
- não enviar memória inteira a providers externos;
- exigir opt-in explícito para enviar contexto relevante ao Gemini;
- manter a opção de envio externo desabilitada por padrão;
- não inventar experiências a partir de inferências;
- mostrar evidências que influenciaram a recomendação.

## Gemini

Uma API Key habilita o provider, não o compartilhamento automático da memória. O envio ocorre
somente quando **Enviar contexto relevante para Gemini** estiver marcado. O payload contém um
resumo das evidências recuperadas para a vaga atual e não inclui o arquivo completo.

## Exclusão e portabilidade

**Apagar memória local** remove o store e o perfil consolidado. Antes disso, a pessoa pode
exportar JSON, JSONL e um resumo Markdown. Importações devem ser revisadas porque passam a
influenciar futuras recomendações.
