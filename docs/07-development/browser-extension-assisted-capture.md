# Browser Extension Assisted Capture

## Objetivo

A extensão assistiva conecta a página atualmente aberta ao SotuHire. Ela atende vagas formais e publicações com oportunidades escondidas, inclusive quando a pessoa usuária já está autenticada em sua própria conta.

## Ações

- **Salvar vaga atual no SotuHire**
- **Analisar vaga atual**
- **Enviar para tracker**

Cada ação exige clique explícito e mostra um preview do conteúdo detectado.

## Fluxo

```text
pessoa abre página
-> clica na extensão
-> extensão extrai conteúdo visível da aba atual
-> pessoa revisa o preview
-> envia ao SotuHire
-> SotuHire normaliza, deduplica, analisa ou salva
```

## Limites técnicos

A extensão não envia cookies, senhas ou tokens ao SotuHire. Ela não percorre automaticamente listas autenticadas, não burla CAPTCHA e não clica em botões nativos de candidatura.

Esses limites preservam controle humano e permitem processar conteúdo que a própria pessoa decidiu abrir e compartilhar.

Para crawling previamente autorizado, o app usa um conector separado:
[Authenticated Browser Crawling](../05-data-sources/authenticated-browser-crawling.md). A captura
assistida não é convertida silenciosamente em crawler autenticado.

## Contrato sugerido

```json
{
  "mode": "USER_ASSISTED_CAPTURE",
  "page_url": "https://platform.example/current-job",
  "title": "Título detectado",
  "visible_text": "Conteúdo revisado da vaga atual",
  "requested_action": "analyze"
}
```

## Evolução

Uma primeira versão pode usar um popup e uma API local. Depois, pode adicionar detecção de página de vaga, post de oportunidade e confirmação de envio ao tracker.
