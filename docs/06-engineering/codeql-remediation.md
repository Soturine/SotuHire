# Processo de remediação CodeQL

CI verde e zero findings são conceitos distintos. O ciclo adotado é: consultar todos os alerts,
agrupar por causa-raiz, corrigir boundaries, executar testes dirigidos, fazer um push consolidado,
aguardar CodeQL e consultar novamente.

Classificações permitidas: TRUE_POSITIVE, PARTIAL_TRUE_POSITIVE, FALSE_POSITIVE, OBSOLETE,
NO_TOUCH_RESIDUAL e DUPLICATE_ROOT_CAUSE. Dismissal exige trace técnico; arquivo protegido exige
mitigação anterior testada. O gate é zero Critical/High verdadeiro, não zero obtido por dismissal.

Os sanitizers centrais são:

- `http_safety`: DNS/IP validado é o mesmo usado na conexão e em redirects;
- `safe_paths`: path resolvido permanece sob root e bloqueia symlink/junction escape;
- `security/url.ts`: comparação estrutural protocol/hostname/origin;
- `browser_inputs`: URL/CDP/argumentos validados antes do launcher no-touch.

