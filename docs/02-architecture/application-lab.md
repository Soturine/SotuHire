# Application Lab

O Application Lab é a camada de orquestração da jornada `/application-lab`. Ele não envia candidaturas e não substitui Perfil, contexto, snapshots ou Tracker. A sessão apenas preserva as escolhas e conecta esses motores em dez etapas revisáveis.

## Fluxo e contratos

`ApplicationLabService` usa `CareerContextEngine`, `ApplicationLabRepository`, `SnapshotStore`, `ApplicationRepository` e `JobTracker`. A API expõe criação, listagem paginada, retomada, atualização, cancelamento, análise, revisão individual de sugestões, variante, kit, plano e salvamento no Tracker.

Uma `ApplicationLabSession` guarda IDs, referências selecionadas, execução, etapa e estado (`draft`, `ready`, `analyzing`, `review`, `completed`, `cancelled` ou `failed`). Alterar currículo, vaga ou contexto invalida somente as etapas 5–10; decisões anteriores continuam auditáveis.

```text
Perfil/contexto confirmado
  + Currículo Mestre
  + JobSnapshot
        ↓
ApplicationLabSession → relatório → sugestões aprovadas
        ↓                    ↓
   variante + kit + plano → snapshots → Tracker
```

## Persistência e continuidade

A migration 5 cria as tabelas do Lab e do Resume Studio com foreign keys, índices, timestamps e validações. A análise cria `AnalysisSnapshot`; o Tracker reutiliza `JobSnapshot` e `ResumeSnapshot` quando já existem e vincula relatório, variante, kit e plano. A interface permite voltar, retomar, reexecutar a análise, trabalhar offline no rascunho e cancelar sem envio externo.

## Limites

- nenhuma etapa executa auto-apply, login, preenchimento ou clique em portal;
- uma sugestão só entra na variante depois de decisão humana;
- o Perfil completo não é enviado pela extensão: somente `capture_id` e `job_snapshot_id`;
- resultado e score não representam probabilidade de entrevista.

Veja também [regras de prontidão](../03-business-rules/application-readiness.md), [snapshots](application-snapshots.md) e [testes](../09-testing/application-lab-testing.md).
