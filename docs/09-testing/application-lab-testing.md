# Testes do Application Lab

A cobertura determinística usa base temporária e dados fictícios. `tests/test_application_lab_service.py` cobre sessão, retomada, invalidação por troca de entrada, análise, relatório multiárea, review/undo, variante, kit, plano, Tracker, snapshots, cancelamento e falha parcial. Repository e API têm suites próprias.

O E2E `application-lab.spec.ts` percorre as dez etapas no modo Demo, confirma que não existe auto-apply, valida revisão humana, diff, artefatos e IDs da extensão. Também verifica mobile e zoom 200%. `visual-v198.spec.ts` captura a mesma jornada para documentação e fica opt-in por `CAPTURE_V198=1`.

Casos multiárea asseguram dimensões aplicáveis, registros profissionais separados e GitHub `not_applicable` fora de vagas técnicas. Testes de injection/segredo permanecem na suíte global.
