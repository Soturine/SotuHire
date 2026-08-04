# Assets de currículo e exports

Currículo Mestre e variantes são identidades distintas. Uma variante referencia o mestre,
a vaga e um change set reversível; nunca sobrescreve o mestre. O Application Kit possui oito
itens revisáveis e exporta somente itens `accepted` ou `edited`.

Professional Assets seguem `draft → review → confirmed`, com `archived` e `stale`. Copiar,
duplicar, editar, rejeitar, desfazer e arquivar são operações explícitas. Regeneração não
apaga decisões humanas.

PDF/DOCX/JSON Resume só incluem blocos habilitados e permitidos para currículo. O export não
inclui trace, prompt, token, chave, caminho pessoal ou evidência sensível. Baixar um arquivo
não envia candidatura nem o publica em serviço externo.
