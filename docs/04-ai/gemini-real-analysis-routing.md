# Gemini na Análise Real

## Três validações

O wizard mantém status separado para:

1. **Ping Gemini**: chamada mínima sem schema.
2. **Structured Output**: valida o JSON Schema real.
3. **Análise real do SotuHire**: usa o mesmo método chamado pelo fluxo do app.

## Chave da sessão

A chave digitada no campo seguro é armazenada somente em `st.session_state` e encaminhada diretamente ao `GeminiProvider`. Ela passa a valer imediatamente, sem exigir salvamento ou reinício.

O resultado mostra:

```text
Análise usada: Gemini ou Local
Modelo: modelo selecionado
Fallback: Sim ou Não
Motivo do fallback: diagnóstico resumido
```

Se Gemini foi selecionado e a chamada real falha, o app usa análise local e explica o motivo. A chave nunca aparece no diagnóstico.
