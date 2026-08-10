# Políticas de matching por domínio

`DomainMatchingPolicy` é uma política determinística sobre as dimensões existentes do Match Engine.
Ela pode alterar peso e aplicabilidade, mas não cria evidência, não usa texto gerado livremente e
não muda os fatos de entrada.

Domínios cobertos: technology, engineering, healthcare, education, law, research,
administration, finance, design, tourism_services, public_exams, early_career e
career_transition.

Fluxo: fatos confirmados → classificação/revisão de domínio → dimensões aplicáveis → pesos
normalizados → score e breakdown. Dimensões não aplicáveis são removidas do denominador, não
tratadas como zero. A API oferece catálogo das políticas e scoring com breakdown reproduzível.

