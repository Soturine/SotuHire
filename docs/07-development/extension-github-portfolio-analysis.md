# Extension GitHub e Portfolio Full Analyzer

O analisador de projetos da v0.9.0 funciona com páginas públicas de perfil GitHub, repositório,
projeto e portfólio. Ele não lê cookies, tokens, localStorage, sessionStorage, headers autenticados
ou GitHub token.

## Dois modos

### Standalone Extension Analysis

A extensão extrai sinais da aba atual e calcula um relatório determinístico no navegador. Uma chave
Gemini standalone pode ser configurada opcionalmente para aprimorar o texto. Essa chave:

- fica somente em `chrome.storage.local`;
- usa uma permissão de host opcional para a chamada Gemini;
- nunca entra no payload enviado ao SotuHire;
- pode ser removida diretamente no popup.

### Connected SotuHire Analysis

A extensão envia os dados públicos para a Local Companion API. O SotuHire:

1. valida o payload;
2. prioriza arquivos centrais;
3. analisa README, arquitetura e commits;
4. calcula os scores;
5. opcionalmente aprimora o texto com Gemini local;
6. salva relatório e evidências na Career Memory.

## Botão injetado e modal

Em repositórios, árvores, arquivos e perfis públicos do GitHub, o content script restrito a
`https://github.com/*` injeta um botão **SotuHire AI**. A inserção tenta primeiro a barra de ações
e usa o cabeçalho como fallback. Um `MutationObserver` reaplica a integração após navegação SPA.

O modal isolado da página mostra score, grade, provider, stack, qualidade do README, commits,
arquitetura, profundidade técnica, manutenção, prontidão para recrutadores, pontos fortes, gaps,
recomendações e evidências para currículo. Também permite copiar, exportar e salvar no SotuHire.

O modo **Deep analysis** aumenta os limites de sinais visíveis amostrados. Ele não desbloqueia
conteúdo privado e não lê dados ocultos.

## Amostragem

Prioridade alta:

- `README.md`, `package.json`, `pyproject.toml`, `requirements.txt`;
- `Dockerfile`, `docker-compose.yml`, `.github/workflows/*`;
- `src/*`, `app/*`, `modules/*`, `tests/*`, `docs/*`.

Ignorados:

- `node_modules`, `dist`, `build`, `.venv`, `__pycache__`;
- imagens, binários, arquivos compactados e locks;
- arquivos acima do limite local de amostragem.

## Scores

- GitHub Profile Score;
- Repository Quality Score;
- Portfolio Score;
- Project Quality Score;
- Recruiter Readiness Score;
- Documentation Score;
- Commit Quality Score;
- Architecture Signal Score;
- Technical Depth Score;
- ATS/Job Evidence Score.

## Memória e vagas

Projetos salvos geram memórias separadas para o relatório principal, evidências, commits e README.
Essas memórias entram no mesmo ranking calibrado usado na análise de vagas, Resume Tailor, Search
Intelligence, Hidden Jobs Radar e perfil profissional.

## Endpoints

```text
POST /capture/github-profile
POST /capture/github-repo
POST /capture/portfolio
POST /capture/project
POST /capture/repo-analysis
POST /capture/commit-analysis
```

## Chrome Web Store

Execute `python scripts/package_extension.py` para validar e gerar
`dist/sotuhire-extension-v0.9.0.zip`. O guia de publicação e os textos da loja ficam em
[`browser-extension/store/`](https://github.com/Soturine/SotuHire/tree/main/browser-extension/store).
