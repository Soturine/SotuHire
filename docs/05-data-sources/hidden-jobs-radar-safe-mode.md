# Hidden Jobs Radar — Safe Mode

## O que entrega

O Hidden Jobs Radar da v0.6.0 é um planejador estratégico. Ele ajuda a procurar oportunidades que podem aparecer em páginas de carreira, comunidades, newsletters e posts públicos, sem coletar conteúdo automaticamente.

Ele sugere:

- empresas coerentes com o perfil;
- cargos equivalentes e termos alternativos;
- fontes para consulta manual;
- alertas que a pessoa usuária pode criar;
- sinais de vaga genérica ou pouco específica.

## O que não faz

O safe mode não:

- raspa LinkedIn ou qualquer portal;
- acessa páginas autenticadas;
- contorna captcha, rate limit ou bloqueios;
- extrai contatos pessoais;
- envia mensagens ou candidaturas;
- afirma que uma oportunidade existe sem evidência.

## Contrato testável

Toda saída inclui `scraping_performed=false`. Esse contrato é coberto por regressão automatizada para evitar que uma evolução futura introduza coleta de rede silenciosa.

## Próxima evolução responsável

Uma versão futura pode aceitar textos e links fornecidos explicitamente pela pessoa usuária, classificar sinais de oportunidade e registrar a origem. Qualquer conector deve ter limites, transparência e revisão humana.
