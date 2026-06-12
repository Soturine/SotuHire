# Follow-up Assistant

O Follow-up Assistant ajuda o usuário a deixar rastro profissional depois de aplicar, sem virar spam.

## Objetivo

Gerar mensagens curtas, revisáveis e contextualizadas para:

- recrutador;
- funcionário da empresa;
- pessoa que publicou a vaga;
- resposta pós-entrevista;
- follow-up educado.

## Regras

- Nunca enviar automaticamente.
- Nunca gerar mensagem em massa sem revisão.
- Nunca fingir intimidade.
- Nunca mentir experiência.
- Nunca pressionar recrutador.
- Sempre manter tom curto e profissional.

## Mensagem pós-candidatura

```text
Olá, [nome]. Tudo bem?

Vi a vaga de [cargo] na [empresa] e me candidatei hoje.
Tenho experiência/interesse em [stack/contexto] e achei a oportunidade alinhada ao meu perfil.

Fico à disposição caso faça sentido conversar.
```

## Follow-up depois de alguns dias

```text
Olá, [nome]. Tudo bem?

Passando só para reforçar meu interesse na vaga de [cargo].
Me candidatei em [data] e sigo à disposição para conversar ou enviar mais informações.

Obrigado pelo retorno quando possível.
```

## Mensagem para post informal

```text
Olá, [nome]. Tudo bem?

Vi sua publicação sobre uma oportunidade em [área/cargo].
Tenho interesse em [stack/área] e gostaria de entender se meu perfil faz sentido para a posição.

Existe um link oficial de candidatura ou posso te enviar meu currículo?
```

## Entrada esperada

```json
{
  "recipient_name": "Nome",
  "company": "Empresa",
  "role": "Cargo",
  "source": "LinkedIn Post",
  "user_strengths": ["Python", "SQL", "projetos de IA"],
  "tone": "profissional_curto",
  "message_type": "post_application"
}
```

## Saída esperada

```json
{
  "message": "...",
  "risk_flags": [],
  "review_required": true
}
```

## Integração com Kanban

Ao gerar mensagem, o SotuHire deve sugerir salvar:

- data;
- destinatário;
- canal;
- status;
- próximo follow-up.

## Checklist de qualidade

- A mensagem tem menos de 700 caracteres?
- A mensagem cita cargo e empresa?
- A mensagem cita uma força real do usuário?
- A mensagem não parece desesperada?
- A mensagem não pede favor exagerado?
- A mensagem não inventa experiência?
