# Threat model local-first

## Ativos e fronteiras

Ativos: currículos, perfil, snapshots, candidaturas, chaves de provider, token de instalação e
sessões. Fronteiras: navegador↔API 8787, extensão↔Companion 8765, parser de documentos,
filesystem/SQLite e provider externo opt-in.

| Ameaça | Controle |
|---|---|
| site malicioso chama localhost | bind loopback, socket/Host/Origin, pairing, cookie HttpOnly, CSRF e CORS restrito |
| brute force/replay/DoS local | proof one-shot com expiração, sessão ligada à origin, rate/body/batch/depth/time limits |
| ZIP bomb/PDF hostil/HTML ativo | assinatura, tamanho descompactado/ratio, páginas, criptografia, parser sem rede e sanitização |
| prompt injection ou exfiltração | dado delimitado como não confiável, scope/opt-in, minimização e logs sanitizados |
| corrupção/perda parcial | transação SQLite, writes atômicos, backup checksummed e JSON quarantine |
| extensão vaza credencial/documento | token em `chrome.storage.session`, service worker, permissões mínimas, handoff por IDs |
| artefato antigo usado como atual | dependency hash, stale explícito e confirmação antes de exportar |

Risco residual: processo local privilegiado ou malware no mesmo usuário pode ler dados locais;
OCR de PDF somente-imagem não é executado automaticamente; provider externo passa a processar
o subconjunto explicitamente autorizado. Nenhum desses riscos é mascarado como isolamento forte.
