# Chrome Web Store Listing

## Nome

SotuHire Assistive Browser Companion

## Categoria sugerida

Produtividade

## Idioma principal

Português (Brasil)

## Proposta

Capturar vagas abertas manualmente, importar candidaturas visíveis e analisar projetos públicos do
GitHub. O modo conectado envia somente o conteúdo capturado para a API local do SotuHire.

## Recursos principais

- botão **SotuHire Insight** em perfis e repositórios públicos do GitHub;
- modal moderno com provider/modelo real, scores, stack, evidências e recomendações;
- captura assistida de vagas em diferentes portais;
- prioridade para `schema.org/JobPosting`, com fallback para conteúdo visível;
- importação paginada com deduplicação;
- análise local, IA configurada no SotuHire ou Gemini/OpenAI próprios opcionais;
- catálogo oficial de modelos com cache e atualização sob demanda;
- handshake com diagnóstico de compatibilidade;
- fila com retry, backoff e export/import sanitizado quando a Companion estiver offline;
- snapshots locais de vaga, edital e análise no modo conectado;
- envio para memória, perfil profissional e tracker local.

## Checklist de publicação

- enviar `dist/sotuhire-extension-v0.9.3.zip`;
- usar as imagens de `store/screenshots/`;
- preencher a política de privacidade com `store/privacy-policy.md`;
- informar que `activeTab`, `scripting`, `storage`, localhost, GitHub público, Gemini e OpenAI são usados;
- executar as instruções de teste antes da revisão.
