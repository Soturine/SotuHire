# Referências externas — base v1.9.9, revisada na v1.10.1

Pesquisa realizada em 3 de agosto de 2026 usando sites oficiais e repositórios originais. O
objetivo foi observar padrões, não copiar branding, layout, texto, código, automação de candidatura,
form filling ou arquitetura SaaS. Nenhum código dessas referências foi incorporado.

| Fonte/versionamento | Licença | Padrão observado | Decisão SotuHire / limitação |
|---|---|---|---|
| [Curricu.lol](https://curricu.lol/) (site consultado em 2026-08-03) | não identificada publicamente na pesquisa | edição de currículo com feedback direto | apenas inspiração de jornada; sem fonte/licença verificável, nada foi copiado |
| [Reactive Resume](https://github.com/AmruthPillai/Reactive-Resume) 5.1.6 | MIT | builder, templates, privacidade/self-host e PDF | adaptou-se a separação editor/preview; UI/arquitetura/código não foram copiados |
| [OpenResume](https://github.com/xitanggg/open-resume) | AGPL-3.0 | parser local, live preview, foco ATS e export | reforçou processamento local; AGPL e layout/código não foram incorporados |
| [JobSync](https://github.com/Gsync/jobsync) 1.1.10 | MIT | tracker, currículos e IA self-hosted | validou continuidade documento→tracker; arquitetura SaaS/fluxos não copiados |
| [Resuml](https://github.com/phoinixi/resuml) 3.1.0 | ISC | dados estruturados no navegador, temas e PDF ATS | reforçou árvore única; formato YAML/UI/código não copiados |
| [Career-Ops](https://github.com/santifer/career-ops) | MIT | local-first, humano no loop, tracker, dedupe e PDF | influenciou aprovação/stale; nenhum texto, layout ou automação copiado |
| [JSON Resume schema](https://jsonresume.org/docs/013-schema-definitions) | MIT para schema/repositório | contrato interoperável de currículo | export compatível com extensões namespaced; não é fonte de verdade interna |

## Plataforma e segurança

- [Chrome Manifest V3](https://developer.chrome.com/docs/extensions/develop/migrate/what-is-mv3):
  service worker sob demanda, código empacotado e permissões mínimas influenciaram a extensão
  0.10.0. Não foram adicionados hosts amplos nem código remoto.
- [OWASP API4:2023](https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/):
  limites de upload, memória, operações, paginação e taxa foram adaptados à API loopback.
- [OWASP CORS guidance](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html):
  origin allowlist e validação de mensagens reforçaram o pairing. Localhost não é tratado
  como identidade ou autorização.

## Bibliotecas de documento

- [pypdf](https://pypi.org/project/pypdf/) e [ReportLab](https://pypi.org/project/reportlab/): extração e rendering PDF em
  memória e texto selecionável. O projeto é AGPL/comercial; o uso e redistribuição devem continuar
  sob revisão de licença. Não se usa o suporte Pro de Office nem se promete layout fiel do original.
- [python-docx 1.2 docs](https://python-docx.readthedocs.io/en/latest/user/quickstart.html) e
  [licença MIT](https://github.com/python-openxml/python-docx/blob/master/LICENSE): criação e
  reabertura de DOCX com parágrafos/estilos. Recursos não suportados e layout pixel-perfect ficam
  fora da promessa.

## Taxonomias e interoperabilidade v1.10.1

| Fonte oficial consultada | Versão/estado | Influência retida |
|---|---|---|
| [CBO — MTE](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/cbo/pagina-inicial/) | CBO 2002, downloads atualizados pelo MTE | ocupação classificatória não equivale a profissão regulamentada |
| [QBQ — MTE](https://qbq.trabalho.gov.br/) | portal oficial consultado em 2026-08-03 | conhecimentos, habilidades e atitudes ligados a ocupações; integração versionada futura |
| [ESCO](https://esco.ec.europa.eu/en/classification) | v1.2.1, 2025-12-10 | conceitos multilíngues e relações ocupação↔skill, nunca verdade automática sobre a pessoa |
| [O*NET](https://www.onetcenter.org/overview.html) | database 30.3; dados em geral CC BY 4.0 com exceções | content model e taxonomy com atribuição/licença por dataset |

Na v1.10.1, o produto entrega contratos e manifestos versionados com checksum,
licença/atribuição, mapping revisável e data de atualização. Bases completas não são baixadas nem
redistribuídas automaticamente; um dataset só é aceito quando sua versão e seu hash são explícitos.
