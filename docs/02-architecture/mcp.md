# MCP local

MCP não é exposto na v2.0. A arquitetura interna já separa tools `read`, `draft` e `write-local`, mas
um servidor MCP só será habilitado quando houver transporte loopback, enable explícito, token,
scopes, ownership e audit testados de ponta a ponta. Scopes de submit/email/login não existirão.

