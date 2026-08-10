# Professional Assets e Application Kit

O domínio `modules/professional_assets` mantém uma biblioteca local de materiais
profissionais reutilizáveis. Ele aceita currículo mestre, variante, carta,
mensagem ao recrutador, bio, seção Sobre, resumo de portfólio, destaque de
projeto e Application Kit. Entrevistas e histórias STAR completas pertencem ao domínio separado
`modules/interviews`, entregue na v1.10.1, para não misturar materiais reutilizáveis com sessões de entrevista.

## Modelo e proveniência

Cada `ProfessionalAsset` preserva conteúdo livre e estruturado, perfil, vaga e
sessão opcionais, `EvidenceScope`, referências de fonte, IDs de evidência,
snapshots documentais e o hash das dependências que produziram o conteúdo.
Edição manual altera apenas o texto e o estado de revisão; a proveniência não é
descartada.

O lifecycle persistido é `draft` → `review` → `confirmed`, com `archived` e
`stale` como estados explícitos. Uma afirmação com conteúdo não pode ser
confirmada sem referência de fonte ou evidência. Mudanças na vaga, no currículo
ou no contexto invalidam os ativos derivados da sessão, mas preservam seus
snapshots para auditoria.

Nenhum ativo atualiza o Perfil Universal, realiza candidatura ou envia dados
automaticamente. O consumidor escolhe quando revisar, confirmar, arquivar,
reutilizar ou exportar.

## Application Kit revisável

O Kit é gerado pelo Application Lab somente depois do bundle independente de
Match, ATS, readiness e Tailor. Ele contém, no mínimo, headline, resumo
profissional, seção Sobre, mensagem curta, carta curta, justificativa da vaga,
destaque de projeto e checklist manual. Quando não existe evidência confirmada,
o campo derivado permanece vazio e traz um aviso — não é preenchido com texto
genérico.

Cada item usa `pending`, `accepted`, `edited`, `rejected` ou `stale`. A
regeneração preserva decisões humanas; o endpoint de exportação inclui somente
itens aceitos ou editados e devolve exatamente o conteúdo revisado. Voltar a
`pending` funciona como desfazer. O mesmo conjunto é registrado como ativos
reutilizáveis vinculados ao hash do bundle.

## API local

- `/api/v1/professional-assets`: criação e listagem paginada;
- `/api/v1/professional-assets/{asset_id}`: leitura e edição;
- `/api/v1/professional-assets/{asset_id}/status`: revisão, confirmação,
  arquivamento, invalidação e desfazer;
- `/api/v1/application-lab/sessions/{session_id}/kit`: criação ou regeneração;
- `/api/v1/application-lab/sessions/{session_id}/kit/items/{item_id}/review`:
  aceitar, editar, rejeitar, desfazer ou marcar stale;
- `/api/v1/application-lab/sessions/{session_id}/kit/export`: conteúdo revisado
  pronto para cópia ou exportação manual.

Todas as mutações passam pelo pareamento, sessão HttpOnly e proteção CSRF da API
local. Veja também [Application Lab](application-lab.md),
[Evidence State e Scope](evidence-state-and-scope.md) e
[Application Analysis Bundle](application-analysis-bundle.md).
