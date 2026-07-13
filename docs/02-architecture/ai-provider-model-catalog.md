# Catálogo de Providers e Modelos de IA

A v1.9.4 consolida a configuração de IA em torno de providers locais seguros, presets de uso e catálogo de modelos. O objetivo é permitir Gemini/OpenAI nos fluxos reais sem expor segredo ao frontend e sem remover o fallback local.

## Escopo

- Providers suportados: `local`, `gemini` e `openai`.
- Alias legado: `openai_future` é normalizado para `openai` com warning seguro.
- Modelos vêm de três camadas: lista builtin versionada, cache local em `data/settings/ai-models-cache.json` e refresh opcional via provider quando houver chave salva.
- Segredos ficam em backend local, preferencialmente em `data/secrets/ai-provider.local.json` ou variável de ambiente local.
- O frontend nunca recebe API key.

## Endpoints

```txt
GET  /api/v1/settings/ai/providers
GET  /api/v1/settings/ai/models?provider=gemini
GET  /api/v1/settings/ai/models?provider=openai
POST /api/v1/settings/ai/models/refresh
```

As respostas listam provider, modelos conhecidos, suporte a JSON/structured output, origem (`builtin`, `cache` ou `provider_api`) e warnings. Elas não retornam segredos.

## Presets

```txt
local_safe -> provider local, use_ai=false, memory_context=false
basic      -> IA para currículo/Lattes, vaga/edital, match, ATS e tailor
complete   -> inclui Radar/Wishlist, Fontes/Extensão e GitHub/Portfólio
custom     -> mantém seleção manual agrupada por áreas
```

Memória local continua desligada por padrão nos presets com IA externa. Quando ativada, o usuário precisa entender que contexto adicional pode ser enviado ao provider.

## Runtime

`apps/api/services/ai_settings.py` é o ponto de seleção do runtime:

- `provider=local` ou `use_ai=false`: fallback local determinístico.
- `provider=gemini`: `GeminiProvider` com o modelo salvo.
- `provider=openai`: `OpenAIProvider` com o modelo salvo.

Fluxos como Editais/Concursos, Lattes, Radar, Match, ATS, Tailor e GitHub/Portfólio devem consultar o runtime pelo backend e respeitar o toggle/preset. Se o provider falhar, a resposta precisa declarar fallback local.

## Testes reais opt-in

Testes com provider externo não rodam no CI por padrão:

```bash
SOTUHIRE_TEST_GEMINI_API_KEY=... pytest -m external_ai
SOTUHIRE_TEST_OPENAI_API_KEY=... pytest -m external_ai
```

Essas chaves não devem ser commitadas, logadas, exibidas em screenshot, fixture ou release notes.

## Segurança

- No app, sem API key no frontend, `localStorage` ou `sessionStorage`; a chave fica no backend.
- Na extensão, chaves próprias opcionais ficam isoladas no service worker, em `chrome.storage.session`
  por padrão ou IndexedDB local após consentimento; isso não implica criptografia adicional e nunca
  usa `chrome.storage.sync`.
- Sem chave em README, docs, fixtures, logs ou screenshots.
- Sem decisão crítica final apenas por IA.
- Sem auto-apply, inscrição automática, pagamento, boleto, envio de documento, login, scraping autenticado ou CAPTCHA bypass.
