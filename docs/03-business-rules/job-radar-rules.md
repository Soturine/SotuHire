# Regras do Radar de Vagas

O Radar de Vagas é local-first e usa o backend/core como fonte de verdade para score, dedupe e
alertas.

## Score

O frontend não calcula score final. O backend considera:

- cargo desejado;
- skills obrigatórias;
- skills desejáveis;
- domínio/indústria;
- senioridade;
- localidade;
- preferência remoto/híbrido/presencial;
- empresas incluídas/excluídas;
- termos excluídos;
- sinais do currículo quando fornecido.

O score é explicável e conservador. Ausência de evidência vira lacuna, não afirmação.

## Alertas

Um alerta pode ser criado quando:

- a wishlist está ativa;
- `notify_on_new_matches=true`;
- a vaga não é duplicata;
- `radar_score >= min_match_score`;
- `ats_score >= min_ats_score`.

Alertas são locais e podem ser marcados como lidos, ignorados ou salvos.

## Deduplicação

Critérios:

- URL normalizada;
- empresa + cargo;
- texto normalizado quando disponível.

Duplicata não deve apagar histórico. A decisão final permanece manual.

## IA opcional

IA pode explicar o match, sugerir tags e resumir lacunas, mas não pode:

- alterar score final;
- inventar requisito;
- inventar experiência;
- inventar salário;
- inventar candidatura;
- ocultar warnings do fallback.

Se a IA falhar, o Radar continua com análise local.

## Ações manuais

O usuário decide quando:

- salvar na Caixa de Entrada;
- salvar no Tracker/Kanban;
- abrir a fonte;
- rodar compatibilidade;
- candidatar-se fora do SotuHire.
