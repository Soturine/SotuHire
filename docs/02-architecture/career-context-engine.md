# Career Context Engine

O Career Context Engine e a camada local-first que monta um contexto unico, compacto e revisavel para os fluxos do SotuHire.

Ele vive em `modules/context` e nao substitui o Perfil Profissional Universal nem a memoria local. A funcao dele e coordenar esses sinais para que Radar, Wishlist, Match, ATS, Tailor, Tracker, Fontes, GitHub/Portfolio, Notificacoes e Dashboard consultem o mesmo contexto por tras.

## Fontes de contexto

O engine usa, quando disponivel:

- Perfil Profissional Universal via `ProfileContextOrchestrator`;
- RAG lexical local via `MemoryRetriever`;
- evidencias de tracker e candidaturas quando ja viraram memoria local;
- oportunidades e fontes importadas quando ja viraram memoria local;
- sinais de GitHub/Portfolio quando ja viraram memoria local;
- preferencias, restricoes, localidades, modelos de trabalho e contratos;
- feedbacks e sinais de aplicacao registrados localmente.

Ele nao cria banco vetorial, servidor externo ou dependencia pesada.

## Propositos

Cada chamada informa um `CareerContextPurpose`:

```txt
generic, wishlist, radar, match, ats, tailor, tracker,
notifications, sources, extension, github, dashboard
```

O proposito ajuda a montar query lexical, limitar evidencias e registrar warnings apropriados.

## Saida

`CareerContext` contem:

- resumo do perfil;
- objetivos;
- areas/dominios;
- senioridade;
- localidades;
- modelos de trabalho;
- tipos de contrato;
- restricoes;
- evidencias com origem, confianca, score, sensibilidade e status de confirmacao;
- warnings;
- notas de privacidade.

## Privacidade

O engine nao inventa fatos. Evidencias sensiveis sao marcadas e os formatadores conseguem omitir esses itens quando o contexto pode ser enviado a provider externo.

Regras principais:

- contexto local completo pode ser usado por regras locais;
- provider externo so recebe contexto quando `allow_memory_context=true`;
- evidencias sensiveis sao omitidas de payload externo;
- itens de baixa confianca aparecem como "a confirmar";
- candidatos de evidencia de GitHub/Portfolio nao entram no perfil sem revisao humana.

## Deduplicacao e prioridade

Evidencias sao deduplicadas por titulo/conteudo normalizado. Quando ha duplicidade, o engine prioriza:

1. confirmado pela pessoa usuaria;
2. alta confianca;
3. score maior;
4. item nao sensivel.

## Consumo por modulo

| Fluxo | Uso esperado |
| --- | --- |
| Wishlist | complementar rascunho com objetivos, dominios, localidades e preferencias confirmadas |
| Radar | usar contexto como sinal local de score e explicacao, sem auto-apply |
| Match | passar evidencias ao Match Engine local e respeitar `allow_memory_context` para provider externo |
| ATS | separar keywords com evidencia local de termos sem suporte |
| Tailor | sugerir ajustes apenas com evidencias reais e linguagem condicional |
| Tracker | retornar resumo, motivo de fit, proxima acao e gaps recorrentes |
| Fontes | classificar alinhamento local e sugerir enviar para Radar, Match ou Tracker sem salvar automaticamente |
| Extensao | usar capturas locais e candidatos revisaveis sem salvar automaticamente no Perfil |
| Notificacoes | melhorar mensagem do Radar com sinais seguros do contexto |
| GitHub/Portfolio | gerar candidatos de evidencia revisaveis para o Perfil |

## Arquivos

```txt
modules/context/__init__.py
modules/context/models.py
modules/context/engine.py
modules/context/formatters.py
tests/test_career_context_engine.py
```
