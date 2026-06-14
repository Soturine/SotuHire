# Regras de captura assistida pelo navegador

## Escopo

A extensão processa a página atual que a pessoa abriu manualmente. Ela pode ler conteúdo visível
em uma sessão onde a própria pessoa já está autenticada, sem receber credenciais e sem automatizar
o login.

O contrato é multiportal: LinkedIn, Gupy, Indeed, InfoJobs, Nube, páginas de carreira e outros
sites usam as mesmas ações e o mesmo pipeline local.

## Ações

- salvar a vaga atual;
- analisar a vaga atual;
- enviar a vaga ao tracker;
- capturar candidaturas visíveis;
- acumular páginas revisadas pela pessoa em um lote;
- pedir ao SotuHire local que use o provider configurado.

## Regras de identidade

- a mesma URL com parâmetros diferentes representa a mesma vaga;
- empresa igual e título fortemente semelhante permitem consolidar URLs de portais diferentes;
- um cartão consolidado preserva todas as URLs e domínios de origem;
- uma candidatura antiga e uma análise posterior enriquecem o mesmo cartão;
- repetir um lote informa quantos itens eram novos e quantos já existiam.

## Limites

- a extensão não faz login e não guarda senha;
- a extensão não burla CAPTCHA ou checkpoint;
- a extensão não recebe chave Gemini;
- o lote máximo aceito pela API contém 500 itens;
- captura e envio continuam ações explícitas no popup.

## Remoção de dados

Os registros ficam em `data/companion/`, `data/sotuhire-opportunities.json`,
`data/sotuhire-history.json` e `data/memory/`. Esses arquivos são locais, ignorados pelo Git e
podem ser removidos ou exportados pela pessoa usuária.
