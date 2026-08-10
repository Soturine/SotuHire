# Atualizações explícitas de taxonomia

O updater de CBO, QBQ, ESCO e O*NET é content-addressed e nunca atualiza silenciosamente.

1. `preview` recebe fonte HTTPS, versão e payload, valida freshness e checksum e grava staging.
2. `apply` exige o `preview_id`; grava snapshot imutável e move o ponteiro ativo.
3. `status` informa versão, checksum, origem, horário e histórico.
4. `rollback` move o ponteiro para uma versão já aplicada; não rebaixa ou apaga arquivos.

Sistema, versão, checksum e preview ID passam pelo boundary de paths confinados. O schema permanece
7 porque o aggregate é um catálogo versionado/content-addressed, não estado relacional concorrente.

