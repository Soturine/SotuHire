# Fluxo de dados v2

Sources/documentos produzem candidates. A Inbox revisa; Profile + Evidence Graph alimentam Career
State; Next Best Actions alimenta planos e propostas; aprovação libera application services; SQLite,
snapshots e audit registram efeito; outcomes voltam ao estado sem alterar pesos automaticamente.

SQLite schema 8 é writer único dos domínios v2. JSON/JSONL serve somente compatibilidade, fixture e
export onde ainda necessário.
