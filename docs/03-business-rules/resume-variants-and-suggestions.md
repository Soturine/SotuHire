# Variantes de currículo e sugestões

O Currículo Mestre é a fonte; cada variante é uma cópia rastreável para uma finalidade ou `job_snapshot_id`. O usuário pode editar, remover, desativar e reordenar na variante sem mutar o mestre.

Cada mudança registra tipo (`added`, `removed`, `edited`, `reordered`), antes, depois, motivo, referências e warning. Sugestões registram seção, evidência, provider run opcional, decisão e valor editado. Apenas itens `accepted` ou `edited` entram na criação da variante.

Uma afirmação nova exige `evidence_used`/`source_refs`; candidato de Perfil continua candidato até confirmação explícita. Undo devolve a decisão para `pending`, não apaga o histórico temporal. Rejeição preserva a sugestão para auditoria.

Exports incluem somente conteúdo habilitado e confirmado. JSON Resume está pronto; PDF/DOCX permanecem pendentes e não recebem arquivo vazio ou sucesso falso.
