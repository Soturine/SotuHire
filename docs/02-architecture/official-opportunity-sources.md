# Fontes oficiais e públicas de oportunidades

Os conectores read-only são Greenhouse Job Board API, Lever Postings API, JSON-LD `schema.org/JobPosting` e RSS/Atom. Todos produzem `OpportunityCandidate` com `source_url`, IDs, datas, hash e `OpportunityProvenance`.

RSS/Atom preserva GUID, ETag e Last-Modified. HTML e JSON-LD são sanitizados. URLs passam por política SSRF: HTTP(S), portas 80/443, sem userinfo, IP/DNS global e redirect revalidado.

Não há autenticação, cookies, captcha, scraping de área privada ou auto-apply. Uma fonte pode ser desativada sem apagar observações já persistidas.
