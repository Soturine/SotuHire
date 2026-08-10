# Contexto e privacidade do Copilot

O Copilot usa contexto selecionado por finalidade, não um dump do banco. Esta política reduz
exposição de dados, custo, ruído e risco de transformar informação irrelevante em recomendação.

## Princípio de minimização

Cada operação declara um purpose, como explicar Career State ou preparar um draft. O selector busca
somente itens compatíveis e registra um context receipt com:

- finalidade;
- quantidade de itens;
- estimativa de tokens;
- se haverá compartilhamento externo;
- quantidade de itens sensíveis omitidos.

O receipt descreve o recorte sem persistir chave de provider ou dado sensível omitido.

## Contexto local e externo

Operações determinísticas e providers locais podem trabalhar sem enviar dados pela internet.
Gemini/OpenAI exigem configuração e opt-in compatível com a ação. Mesmo após opt-in, o selector não
envia o banco inteiro.

Contexto externo privilegia evidências confirmadas e não sensíveis. Candidatos, rejected, stale e
registros sensíveis ficam fora por padrão.

## Dados sensíveis

Número de registro profissional, identificadores pessoais e conteúdo marcado como sensível não
entram automaticamente em prompt. Se uma tarefa futura realmente exigir um campo sensível, a UI e
o contrato deverão tornar finalidade e seleção explícitas; a v2.0 não presume essa autorização.

## Conteúdo não confiável

Vaga, currículo, PDF, README, link ou portfólio podem entrar como dados do contexto, mas instruções
contidas neles não alteram system rules, registry ou approval status. Context building separa
conteúdo do usuário de comandos do sistema.

## Providers e segredos

Chaves de Gemini/OpenAI ficam no backend local. Frontend, context receipt, proposta, audit,
benchmark, export e pacote da extensão não devem conter o valor. Diagnósticos retornam categorias e
request IDs sanitizados.

Provider output é validado por schema. Falha, quota ou timeout gera erro tipado/fallback quando
suportado, sem relaxar a approval boundary.

## Context budget

Token estimate torna o tamanho do recorte observável. O sistema deve preferir resumos e evidências
diretamente relacionadas à finalidade. Aumentar contexto indiscriminadamente não é estratégia de
qualidade: pode reduzir precisão e ampliar exposição.

## Audit e retenção

Audit registra finalidade, referências e efeitos necessários para explicar uma decisão. Ele não
armazena chain-of-thought nem precisa duplicar o prompt completo. Outputs de provider seguem os
stores e políticas do fluxo consumidor; IA não cria um segundo perfil autoritativo.

## Busca universal

Busca universal v2 opera sobre dados locais compatíveis com o modo atual. Ela não envia o índice
para serviço externo e deve respeitar sensibilidade/visibilidade ao apresentar resultados.

## Controles do usuário

- escolher provider ou continuar local;
- revisar contexto e evidências consideradas;
- não aprovar uma proposta;
- rejeitar ou marcar stale uma evidência;
- excluir chave configurada pelo mecanismo próprio;
- manter item de portfólio privado;
- fazer backup antes de migration/restore.

## Limites

- local-first não protege contra malware com acesso ao dispositivo;
- opt-in não torna todo dado adequado para compartilhamento;
- provider externo mantém sua própria política de processamento;
- o SotuHire não promete anonimização perfeita de texto livre;
- usuário deve remover dados confidenciais de documentos antes de importá-los quando necessário.

## Links relacionados

- [Human-Approved Career Copilot](../02-architecture/human-approved-copilot.md)
- [Evidence Graph](../02-architecture/evidence-graph.md)
- [Threat model v2](../06-engineering/v2-security-threat-model.md)
- [Estratégia de providers](provider-strategy.md)
- [Guia do usuário](../05-user-guide/career-workflow.md#privacidade-e-segurança)
