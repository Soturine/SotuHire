# Career Context Engine

O Career Context Engine é a camada local-first que monta um contexto único, compacto e revisável para os fluxos do SotuHire.

Ele vive em `modules/context` e não substitui o Perfil Profissional Universal nem a memória local. A função dele é coordenar esses sinais para que Radar, Wishlist, Match, ATS, Tailor, Tracker, Fontes, GitHub/Portfólio, Lattes/acadêmico, Editais/Concursos, Extensão, Notificações e Dashboard consultem o mesmo contexto por trás.

## Fontes de Contexto

O engine usa, quando disponível:

- Perfil Profissional Universal via `ProfileContextOrchestrator`;
- evidências acadêmicas/Lattes confirmadas no Perfil Universal;
- RAG lexical local via `MemoryRetriever`;
- evidências de tracker e candidaturas quando já viraram memória local;
- oportunidades e fontes importadas quando já viraram memória local;
- sinais de GitHub/Portfólio quando já viraram memória local;
- preferências, restrições, localidades, modelos de trabalho e contratos;
- feedbacks e sinais de aplicação registrados localmente.

Ele não cria banco vetorial, servidor externo ou dependência pesada.

## Propósitos

Cada chamada informa um `CareerContextPurpose`:

```txt
generic, wishlist, radar, match, ats, tailor, tracker,
notifications, sources, extension, github, dashboard,
academic, lattes, public_exams
```

O propósito ajuda a montar query lexical, limitar evidências e registrar warnings apropriados.

## Saída

`CareerContext` contém:

- resumo do perfil;
- objetivos;
- áreas/domínios;
- senioridade;
- localidades;
- modelos de trabalho;
- tipos de contrato;
- restrições;
- evidências com origem, confiança, score, sensibilidade e status de confirmação;
- warnings;
- notas de privacidade.

## Privacidade

O engine não inventa fatos. Evidências sensíveis são marcadas e os formatadores conseguem omitir esses itens quando o contexto pode ser enviado a provider externo.

Regras principais:

- contexto local completo pode ser usado por regras locais;
- provider externo só recebe contexto quando `allow_memory_context=true`;
- evidências sensíveis são omitidas de payload externo;
- itens de baixa confiança aparecem como “a confirmar”;
- candidatos de evidência de GitHub/Portfólio, extensão ou Lattes não entram no Perfil sem revisão humana.

## Deduplicação e Prioridade

Evidências são deduplicadas por título/conteúdo normalizado. Quando há duplicidade, o engine prioriza:

1. confirmado pela pessoa usuária;
2. alta confiança;
3. score maior;
4. item não sensível.

## Consumo por Módulo

| Fluxo | Uso esperado |
| --- | --- |
| Wishlist | complementar rascunho com objetivos, domínios, localidades e preferências confirmadas |
| Radar | usar contexto como sinal local de score e explicação, sem auto-apply |
| Match | passar evidências ao Match Engine local e respeitar `allow_memory_context` para provider externo |
| ATS | separar keywords com evidência local de termos sem suporte, incluindo evidências acadêmicas |
| Tailor | sugerir ajustes apenas com evidências reais e linguagem condicional |
| Tracker | retornar resumo, motivo de fit, próxima ação e gaps recorrentes |
| Fontes | classificar alinhamento local e sugerir enviar para Radar, Match ou Tracker sem salvar automaticamente |
| Extensão | usar capturas locais e candidatos revisáveis sem salvar automaticamente no Perfil |
| Lattes/acadêmico | incluir formação, pesquisa, publicações, extensão e docência confirmadas no Perfil |
| Notificações | melhorar mensagem do Radar com sinais seguros do contexto |
| GitHub/Portfólio | gerar candidatos de evidência revisáveis para o Perfil |
| Editais/Concursos | comparar requisitos de edital com formação, títulos, registros, certificações, experiência, localização e evidências acadêmicas/Lattes confirmadas |

Na v1.9.4, a extensão pode consultar apenas um resumo seguro desse contexto. Esse resumo indica se há Perfil disponível, fluxos habilitados e status de IA, mas não retorna o Perfil inteiro, memória completa ou segredo de provider.

## Public exams

A partir da v1.9.3, `CareerContextPurpose.PUBLIC_EXAMS` é usado pelo módulo `modules/public_exams` no endpoint:

```txt
POST /api/v1/public-exams/{notice_id}/analyze
```

O contexto de editais inclui sinais confirmados do Perfil Profissional Universal, especialmente:

- formação concluída ou em andamento;
- registros profissionais confirmados;
- certificações;
- experiência profissional;
- localização e disponibilidade;
- preferências de contrato/regime;
- evidências acadêmicas/Lattes, como pesquisa, extensão, docência, publicações, bolsas e produção técnica.

Regras importantes:

- edital não adiciona formação, registro ou certificação ao Perfil;
- requisitos legais sem evidência viram `missing` ou `uncertain`;
- graduação em andamento não passa como graduação concluída;
- registro profissional não é presumido;
- o score usa linguagem condicional e não substitui a leitura oficial do edital.

## Arquivos

```txt
modules/context/__init__.py
modules/context/models.py
modules/context/engine.py
modules/context/formatters.py
tests/test_career_context_engine.py
```
