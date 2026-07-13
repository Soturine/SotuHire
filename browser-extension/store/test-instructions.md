# Instruções para revisão

## Modo independente

1. Carregue a pasta descompactada em um Chromium compatível.
2. Abra um repositório público em `https://github.com/{owner}/{repo}`.
3. Confirme o botão **SotuHire Insight** próximo às ações ou ao cabeçalho.
4. Abra o modal e execute a análise local, sem chave.
5. Confirme score, provider/modelo local, evidências e ausência de erro.

## Providers opcionais

1. No popup, abra **IA** e selecione Gemini ou OpenAI.
2. Confirme o link oficial, campo mascarado, persistência desmarcada e catálogo builtin.
3. Se o revisor possuir uma chave temporária própria, valide o catálogo e um modelo.
4. Confirme que o modelo escolhido aparece no trace do relatório.
5. Use **Remover chave** ao terminar.

Não fornecemos chave de teste e nenhuma chave deve aparecer em screenshot, log ou exportação.

## Modo conectado

1. Inicie `python -m modules.local_api.server`.
2. Abra **Conexão local avançada > Diagnóstico de compatibilidade**.
3. Confirme extensão, Companion, API, capabilities e `compatible=true`.
4. Abra uma página de vaga fictícia e use **Salvar vaga**.
5. Confirme a resposta local e o `snapshot_id` no histórico do SotuHire.
6. Capture um edital e confirme que ele fica pendente de revisão.

## Fila offline

1. Desligue a Companion.
2. Capture novamente uma vaga fictícia.
3. Confirme que a ação fica na fila sem perda do payload.
4. Abra **Lotes e modo offline** e teste o retry.
5. Exporte a fila e confirme ausência de chaves, tokens e cookies.
6. Importe o mesmo arquivo e confirme que a URL não duplica.

Não é necessário login para testar GitHub público. A extensão não deve clicar em candidatura,
coletar cookie ou solicitar acesso a toda a navegação.
