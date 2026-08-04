# Estado de revisão de evidância

`EvidenceReviewStatus` é `candidate`, `sourced`, `confirmed`, `rejected` ou `stale`.

- `candidate`: inferência/sugestão ainda sem origem suficiente;
- `sourced`: extraído de uma fonte identificada, ainda não confirmado pela pessoa;
- `confirmed`: revisado e aceito explicitamente;
- `rejected`: revisado e recusado; não reaparece como fato por reimportação;
- `stale`: dependências mudaram; permanece auditável, mas não é reutilizado silenciosamente.

`EvidenceScope` é uma decisão separada: perfil, currículo, match, ATS, tailor, kit e provider
externo podem ter permissões diferentes. Somente evidência confirmada, selecionada, não sensível
e com opt-in pode sair para provider. Rejeição/stale prevalecem sobre origem e deduplicação.
