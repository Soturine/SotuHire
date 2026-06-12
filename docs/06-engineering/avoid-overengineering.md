# Evitando overengineering

## Definição

Overengineering acontece quando o projeto fica mais complexo do que o problema atual exige. No SotuHire, isso seria adicionar tecnologias, padrões e camadas antes de validar a análise básica.

## Não começar com

- microserviços;
- Kubernetes;
- fila distribuída;
- autenticação completa;
- React + FastAPI no primeiro dia;
- PostgreSQL antes de precisar;
- crawler complexo;
- extensão Chrome antes do MVP;
- múltiplos provedores de IA antes de funcionar com um;
- sistema de usuários;
- pagamentos;
- deploy complexo.

## Começar com

- Streamlit;
- Python;
- módulos simples;
- `.env`;
- PDF parser;
- uma API de IA;
- JSON estruturado;
- testes de regra de negócio;
- documentação clara.

## Sinais de que está virando overengineering

- você passa mais tempo configurando infra do que melhorando o match;
- uma mudança simples exige mexer em muitos arquivos;
- existem classes que só têm um método e não resolvem problema real;
- o README promete mais do que o código faz;
- não há testes, mas há arquitetura complexa;
- o projeto depende de cinco serviços para rodar localmente.

## Quando evoluir a arquitetura

Evolua quando houver dor real:

- Streamlit ficou limitado;
- histórico local precisa virar multiusuário;
- buscas precisam rodar em background;
- fontes de vagas ficaram numerosas;
- há necessidade de API pública;
- deploy precisa separar frontend/backend.

## Regra prática

> Simples não é mal feito. Simples é o mínimo necessário bem organizado.
