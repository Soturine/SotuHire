# Captura assistida pela extensão

## Objetivo

A extensão conecta a página aberta ao SotuHire sem transformar o navegador em crawler. Ela atende
vagas, editais, candidaturas já realizadas e projetos públicos com ações iniciadas pela pessoa.

## Fluxo atual

```text
pessoa abre a página
-> escolhe capturar, analisar, copiar ou enviar
-> content script lê JSON-LD/sinais semânticos/texto visível
-> popup mostra o resultado ou cria pendência offline
-> Local Companion valida e cria snapshot
-> site oferece importação, Tracker ou candidatos revisáveis
```

As ações principais são:

- salvar ou analisar a vaga atual;
- enviar ao Tracker;
- capturar edital para revisão;
- copiar texto visível;
- acumular candidaturas já realizadas em lote;
- analisar GitHub/portfólio localmente ou com provider escolhido;
- enviar projetos ao SotuHire e gerar candidatos para o Perfil.

## Extração

Vagas priorizam `schema.org/JobPosting`. Se o JSON-LD estiver ausente ou inválido, seletores
semânticos e texto visível mantêm a captura funcional. O payload registra a estratégia e preserva
os dados estruturados usados.

No GitHub, o content script permanente é restrito a `https://github.com/*`. Em outros sites, o
extrator roda somente na aba ativa depois do clique no popup; não há permissão `<all_urls>`.

## Modo independente e conectado

Sem backend, a extensão copia a página e analisa projetos com o motor determinístico ou uma chave
própria Gemini/OpenAI. Com a Companion, ela salva capturas, usa contexto seguro, cria snapshots,
envia ao Tracker e integra com o Perfil.

Falhas conectadas entram na fila local. A fila deduplica URL, usa retry com backoff e limite,
registra erros e pode ser exportada/importada sem credenciais.

## Limites técnicos

A extensão não envia cookie, senha, token, sessão, header autenticado ou storage de terceiros. Ela
não percorre listas, não burla CAPTCHA e não clica em candidatura. O próprio usuário decide qual
página compartilhar e qual ação executar.

O authenticated-browser é um conector separado. A captura assistida nunca é convertida
silenciosamente em crawling autenticado.

## Contrato de captura

```json
{
  "kind": "job",
  "page_title": "Título visível",
  "url": "https://jobs.example/vaga/42",
  "visible_text": "Conteúdo visível revisável",
  "job_title": "Título estruturado",
  "company": "Organização",
  "location": "Local",
  "description": "Descrição",
  "extraction_strategy": "schema_org_jobposting",
  "structured_data": {},
  "collection_method": "browser_assisted_capture"
}
```

O Companion devolve `capture_id` e `snapshot_id`. Análises posteriores preservam provider, modelo,
prompt, evidências e fallback sem alterar a captura original.

## Referências

- `browser-extension/README.md`
- [Local Companion API](../02-architecture/local-companion-api.md)
- [Regras de captura](../03-business-rules/browser-assisted-capture-rules.md)
- [Testes](../09-testing/browser-extension-testing.md)
