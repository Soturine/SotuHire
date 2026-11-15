/**
 * Readable names for Universal Profile item types and sources. Academic types mirror
 * `_ACADEMIC_TYPE_LABELS` in modules/academic/lattes_parser.py; anything unknown is humanized
 * ("field_work" -> "Field work") instead of shown raw.
 */
const TYPE_LABEL: Record<string, string> = {
  academic_advising: "Orientação acadêmica",
  academic_profile: "Perfil acadêmico",
  artistic_production: "Produção artística",
  award: "Prêmio ou título",
  book: "Livro",
  book_chapter: "Capítulo de livro",
  certificate: "Certificação",
  certification: "Certificação",
  clinical_practice: "Prática clínica",
  cnpq_area: "Área CNPq",
  conference_paper: "Trabalho em anais",
  constraint: "Restrição",
  course: "Curso",
  course_taught: "Curso ministrado",
  curriculum_lattes: "Currículo Lattes informado",
  dataset: "Dataset",
  doctorate: "Doutorado",
  education: "Formação",
  event_participation: "Participação em evento",
  exam_board: "Banca",
  experience: "Experiência",
  extension_project: "Projeto de extensão",
  field_work: "Trabalho de campo",
  grant: "Fomento",
  higher_education: "Formação superior",
  internship: "Estágio",
  journal_article: "Artigo em periódico",
  laboratory_practice: "Prática de laboratório",
  language: "Idioma",
  lattes_identifier: "Identificador Lattes",
  lecture: "Palestra",
  license: "Registro profissional",
  master_degree: "Mestrado",
  mba: "MBA",
  monitoring: "Monitoria",
  orcid: "ORCID",
  patent: "Patente",
  portfolio: "Portfólio",
  portfolio_academic: "Portfólio acadêmico",
  postdoc: "Pós-doutorado",
  postgraduate_education: "Pós-graduação",
  presentation: "Apresentação de trabalho",
  professional_bio: "Apresentação profissional",
  professional_registry: "Registro profissional",
  project: "Projeto",
  publication: "Publicação",
  research_area: "Área ou linha de pesquisa",
  research_project: "Projeto de pesquisa",
  reviewer_activity: "Atividade de revisão",
  scholarship: "Bolsa",
  scientific_initiation: "Iniciação científica",
  short_course: "Curso de curta duração",
  skill: "Competência",
  skills: "Competências",
  software_registration: "Registro de software",
  specialization: "Especialização",
  target_role: "Cargo-alvo",
  teaching_assistant: "Assistência docente",
  teaching_experience: "Experiência docente",
  teaching_project: "Projeto de docência",
  technical_education: "Formação técnica",
  technical_production: "Produção técnica",
  technical_report: "Relatório técnico",
  technical_skill: "Competência técnica",
  volunteer: "Voluntariado",
  volunteer_work: "Voluntariado",
};

const SOURCE_LABEL: Record<string, string> = {
  manual: "Informado por você",
  manual_notes: "Notas manuais",
  manual_text: "Texto informado por você",
  resume: "Currículo importado",
  local_upload: "Arquivo enviado",
  curriculum_lattes: "Lattes",
  lattes: "Lattes",
  portfolio: "Portfólio",
  portfolio_capture: "Captura de portfólio",
  github_capture: "GitHub",
  extension_capture: "Extensão do navegador",
  certificate: "Certificado",
  ai: "Sugestão de IA",
  fallback: "Extração local",
  demo: "Exemplo",
  demo_resume: "Currículo de exemplo",
  demo_manual: "Exemplo informado",
};

function humanize(value: string): string {
  const text = value.replaceAll("_", " ").trim();
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : value;
}

export function profileTypeLabel(type: string): string {
  return TYPE_LABEL[type] ?? humanize(type);
}

export function profileSourceLabel(source: string | null | undefined): string {
  if (!source) return "Informado por você";
  return SOURCE_LABEL[source] ?? humanize(source);
}
