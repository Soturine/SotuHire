# SotuHire Assistive Browser Companion

Extensão Manifest V3 para capturar a página atual ou uma lista visível de candidaturas e enviar os
dados para a Local Companion API em `http://127.0.0.1:8765`.

## Instalação local

1. Abra a página de extensões do Chromium.
2. Ative o modo desenvolvedor.
3. Escolha **Carregar sem compactação**.
4. Selecione a pasta `browser-extension/`.
5. Inicie a Local Companion API pela aba **Extensão** no SotuHire.

## Privacidade

- usa somente `activeTab`, `scripting` e `storage`;
- processa a página que a pessoa abriu manualmente;
- não automatiza login e não guarda senha;
- não burla CAPTCHA;
- não armazena API Key;
- o modo IA apenas pede à API local que use o provider configurado no SotuHire.
