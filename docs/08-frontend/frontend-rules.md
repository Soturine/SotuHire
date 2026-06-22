# Frontend rules

## O que o frontend pode fazer

- renderizar telas e estados;
- chamar endpoints;
- validar campos obrigatórios;
- organizar fluxo de uso;
- mostrar gráficos com dados recebidos da API;
- guardar preferências visuais não sensíveis;
- exibir mocks em modo demo.

## O que o frontend não pode fazer

- calcular Match Score real;
- inferir competências como possuídas;
- inventar experiência, formação, cargo, certificação ou registro;
- executar análise ATS real sem backend/core;
- recriar Resume Tailor com lógica própria;
- guardar Gemini key, GitHub token ou segredos em bundle público;
- acessar fontes autenticadas sem ação explícita;
- prometer que GitHub Pages roda backend.

## Regras anti-invenção

O frontend deve preservar a separação:

- presente com evidência;
- ausente mas seguro de adicionar se for verdadeiro;
- ausente sem evidência;
- gap crítico.

## Local-first

O frontend moderno deve assumir que o usuário pode rodar o app localmente. Integrações
externas devem ser opcionais, explícitas e visíveis.

## GitHub Pages

GitHub Pages é vitrine estática, documentação e demo visual. Não é backend, não executa
Python e não deve receber dados sensíveis.

