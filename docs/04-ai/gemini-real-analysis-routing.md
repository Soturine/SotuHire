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

## Extensão e extração de currículo na v0.9.0

A extensão nunca recebe a API Key. O popup envia somente a intenção `use_ai`; a Local Companion
API usa o provider configurado no SotuHire e retorna apenas scores, recomendação e nome do provider.

Na aba de currículo, a pessoa também pode permitir explicitamente uma extração estruturada pelo
Gemini. O resultado é mesclado com o parser local e continua sujeito a revisão. Se a chamada falha,
o perfil local é mantido.
