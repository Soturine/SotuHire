# Application Analysis Bundle

O Application Lab v1.9.9 executa quatro produtos de domínio independentes. Nenhum valor é
renomeado para representar outro conceito:

1. `application_match` chama o Match Engine 2 local e persiste o `MatchResultV2` exato;
2. `application_ats` chama as regras ATS locais e persiste score, problemas e keywords;
3. `application_readiness` calcula preparação operacional, cobertura e confiança separadamente;
4. `application_tailor` chama o Tailor seguro e persiste apenas sugestões baseadas em evidência.

Os quatro snapshots imutáveis são ligados por um `ApplicationAnalysisBundle`. O bundle guarda o
`EvidenceScope` efetivamente aplicado e um `dependency_hash` calculado sobre Currículo Mestre,
snapshot da oportunidade, seleção de evidências e versões dos motores. O Tracker recebe os IDs
de Match, ATS, Readiness e Tailor em campos próprios.

## Seleção e invalidação

- Entradas do currículo só entram na análise quando estão `confirmed` e pertencem à seleção.
- `source_ref` é proveniência; sozinho não confirma um fato.
- Evidências `candidate`, `sourced`, `rejected` ou `stale` não alimentam Match/Tailor como fatos.
- Alterar currículo, vaga ou seleção marca o bundle anterior como `stale`, preserva seus
  snapshots e limpa os vínculos derivados da sessão.
- Conflitos ao aplicar sugestões ficam em avisos e não entram no `change_set` da variante.

Os providers externos não participam desse fallback. O caminho local usa os parsers e motores
determinísticos reais, sem `MockProvider` e sem transformar ausência de credencial em sucesso.
