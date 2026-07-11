export const DEMO_PERSONA_STORAGE_KEY = "sotuhire-demo-persona";

export interface DemoPersona {
  id: string;
  label: string;
  headline: string;
  summary: string;
  domains: string[];
  careerMoments: string[];
  targetRoles: string[];
  seniority: string[];
  locations: string[];
  workModels: string[];
  contractTypes: string[];
  evidence: Array<{
    type: string;
    title: string;
    description: string;
    source: string;
    sourceRef?: string;
    skills: string[];
  }>;
  opportunity: { title: string; organization: string; source: string; requirements: string[] };
  wishlist: { name: string; skills: string[] };
  notification: string;
  context: string;
}

export const DEMO_PERSONAS: DemoPersona[] = [
  {
    id: "engineering-student",
    label: "Estudante de Engenharia",
    headline: "Estudante de engenharia com projetos acadêmicos",
    summary: "Busca estágio técnico usando projetos, laboratório e relatórios como evidência.",
    domains: ["Engenharia", "Tecnologia"],
    careerMoments: ["estudante", "estágio"],
    targetRoles: ["Estágio em Engenharia", "Assistente Técnico"],
    seniority: ["estágio"],
    locations: ["São José dos Campos", "Remoto"],
    workModels: ["híbrido", "remoto"],
    contractTypes: ["estágio"],
    evidence: [
      {
        type: "higher_education",
        title: "Engenharia em andamento",
        description: "Graduação fictícia com laboratório e projeto integrador.",
        source: "demo_resume",
        skills: ["relatórios técnicos", "Excel", "Python"],
      },
    ],
    opportunity: {
      title: "Estágio em Engenharia de Processos",
      organization: "Indústria Exemplo",
      source: "Radar público",
      requirements: ["Excel", "qualidade", "relatórios"],
    },
    wishlist: { name: "Estágios de engenharia", skills: ["Excel", "qualidade", "Python"] },
    notification: "Novo estágio alinhado ao projeto integrador.",
    context: "Formação em andamento e projeto acadêmico confirmados.",
  },
  {
    id: "nursing",
    label: "Profissional de Enfermagem",
    headline: "Enfermeira assistencial com COREN confirmado",
    summary: "Organiza experiência clínica, registro profissional e educação continuada.",
    domains: ["Saúde", "Enfermagem"],
    careerMoments: ["experiência formal"],
    targetRoles: ["Enfermeira Assistencial", "Enfermeira UTI"],
    seniority: ["pleno"],
    locations: ["São Paulo"],
    workModels: ["presencial"],
    contractTypes: ["CLT"],
    evidence: [
      {
        type: "professional_registry",
        title: "COREN ativo — exemplo fictício",
        description: "Registro profissional fictício confirmado para a demonstração.",
        source: "demo_manual",
        sourceRef: "demo-coren-001",
        skills: ["segurança do paciente", "prontuário"],
      },
    ],
    opportunity: {
      title: "Enfermeira UTI",
      organization: "Hospital Exemplo",
      source: "Página pública",
      requirements: ["COREN", "UTI", "segurança do paciente"],
    },
    wishlist: { name: "Enfermagem hospitalar", skills: ["COREN", "UTI"] },
    notification: "Vaga hospitalar com COREN e escala a revisar.",
    context:
      "Registro profissional confirmado; escala e experiência específica precisam de revisão.",
  },
  {
    id: "researcher",
    label: "Pesquisador com Lattes",
    headline: "Pesquisador em dados ambientais e iniciação científica",
    summary: "Conecta Lattes, publicação, projeto de pesquisa e produção técnica ao Perfil.",
    domains: ["Pesquisa", "Dados"],
    careerMoments: ["iniciação científica", "pós-graduação"],
    targetRoles: ["Pesquisador Júnior", "Analista de Pesquisa"],
    seniority: ["júnior"],
    locations: ["Brasil", "Remoto"],
    workModels: ["híbrido"],
    contractTypes: ["bolsa", "CLT"],
    evidence: [
      {
        type: "journal_article",
        title: "Artigo fictício sobre dados ambientais",
        description: "Publicação demo importada do Lattes e confirmada manualmente.",
        source: "curriculum_lattes",
        sourceRef: "10.1234/sotuhire.demo",
        skills: ["Python", "análise de dados", "escrita científica"],
      },
    ],
    opportunity: {
      title: "Bolsa de Pesquisa em Dados",
      organization: "Instituto Exemplo",
      source: "Chamada pública",
      requirements: ["Python", "Lattes", "produção científica"],
    },
    wishlist: { name: "Pesquisa aplicada", skills: ["Python", "Lattes", "estatística"] },
    notification: "Chamada de pesquisa relacionada à publicação confirmada.",
    context: "Publicação com DOI e projeto de pesquisa confirmados pelo usuário.",
  },
  {
    id: "teacher",
    label: "Professor / Licenciatura",
    headline: "Professora licenciada com docência e extensão",
    summary: "Demonstra prática docente, projeto de extensão e formação continuada.",
    domains: ["Educação", "Docência"],
    careerMoments: ["docência"],
    targetRoles: ["Professora de Ciências", "Educadora de Projetos"],
    seniority: ["pleno"],
    locations: ["Campinas"],
    workModels: ["presencial", "híbrido"],
    contractTypes: ["CLT", "temporário"],
    evidence: [
      {
        type: "teaching_experience",
        title: "Projeto de ensino e extensão",
        description: "Oficinas fictícias de ciências com planejamento e avaliação.",
        source: "curriculum_lattes",
        sourceRef: "demo-lattes-teaching",
        skills: ["planejamento de aula", "extensão", "avaliação"],
      },
    ],
    opportunity: {
      title: "Professora de Ciências",
      organization: "Escola Exemplo",
      source: "Portal público",
      requirements: ["licenciatura", "docência", "planejamento"],
    },
    wishlist: { name: "Docência e extensão", skills: ["licenciatura", "planejamento"] },
    notification: "Oportunidade docente relacionada ao projeto de extensão.",
    context: "Docência e extensão são evidências acadêmicas, não cargos corporativos inventados.",
  },
  {
    id: "career-transition",
    label: "Transição de Carreira",
    headline: "Pessoa em transição com experiência comunitária",
    summary: "Valoriza experiência não formal e competências transferíveis sem criar cargos.",
    domains: ["Operações", "Atendimento"],
    careerMoments: ["transição"],
    targetRoles: ["Assistente de Operações", "Atendimento ao Cliente"],
    seniority: ["júnior"],
    locations: ["Recife", "Remoto"],
    workModels: ["remoto", "híbrido"],
    contractTypes: ["CLT"],
    evidence: [
      {
        type: "volunteer_work",
        title: "Organização de feira comunitária",
        description: "Coordenou agenda, comunicação e planilhas em atividade voluntária fictícia.",
        source: "demo_manual",
        skills: ["organização", "comunicação", "planilhas"],
      },
    ],
    opportunity: {
      title: "Assistente de Operações",
      organization: "Serviço Exemplo",
      source: "Importação manual",
      requirements: ["organização", "Excel", "atendimento"],
    },
    wishlist: { name: "Primeira oportunidade formal", skills: ["organização", "atendimento"] },
    notification: "Vaga júnior com competências transferíveis para revisar.",
    context: "Experiência comunitária confirmada; nenhuma experiência formal presumida.",
  },
  {
    id: "public-exam",
    label: "Candidato a Concurso",
    headline: "Candidato organizando edital e plano de estudo",
    summary: "Usa Perfil, Exam Fit, checklist e estudo sem automatizar inscrição.",
    domains: ["Administração Pública"],
    careerMoments: ["concurso público"],
    targetRoles: ["Analista Administrativo"],
    seniority: ["nível superior"],
    locations: ["Brasília"],
    workModels: ["presencial"],
    contractTypes: ["estatutário"],
    evidence: [
      {
        type: "higher_education",
        title: "Graduação em Administração — demo",
        description: "Formação fictícia confirmada para comparar requisitos do edital.",
        source: "demo_resume",
        skills: ["administração", "português", "Excel"],
      },
    ],
    opportunity: {
      title: "Edital 01/2026 — Analista Administrativo",
      organization: "Órgão Exemplo",
      source: "Edital público",
      requirements: ["graduação", "português", "administração pública"],
    },
    wishlist: { name: "Concursos administrativos", skills: ["português", "administração"] },
    notification: "Prazo do edital fictício se aproxima; confira a fonte oficial.",
    context: "Formação confirmada; documentos, prazos e elegibilidade exigem revisão oficial.",
  },
  {
    id: "designer",
    label: "Artista / Design",
    headline: "Designer visual com portfólio público",
    summary: "Organiza projetos visuais, processo criativo e entregas de portfólio.",
    domains: ["Design", "Artes"],
    careerMoments: ["portfólio"],
    targetRoles: ["Designer Visual", "Ilustradora"],
    seniority: ["júnior"],
    locations: ["Rio de Janeiro", "Remoto"],
    workModels: ["remoto", "freelance"],
    contractTypes: ["PJ", "freelance"],
    evidence: [
      {
        type: "portfolio",
        title: "Identidade visual para festival fictício",
        description: "Projeto demo com pesquisa, sistema visual e peças digitais.",
        source: "portfolio_capture",
        sourceRef: "https://portfolio.example/festival",
        skills: ["identidade visual", "Figma", "ilustração"],
      },
    ],
    opportunity: {
      title: "Designer Visual Júnior",
      organization: "Estúdio Exemplo",
      source: "Portfólio / página pública",
      requirements: ["Figma", "identidade visual", "portfólio"],
    },
    wishlist: { name: "Design e ilustração", skills: ["Figma", "identidade visual"] },
    notification: "Projeto de design alinhado a uma oportunidade de portfólio.",
    context: "Projeto visual confirmado e fonte pública preservada.",
  },
];

export function getActiveDemoPersona(): DemoPersona {
  if (typeof window === "undefined") return DEMO_PERSONAS[0]!;
  const selected = window.localStorage.getItem(DEMO_PERSONA_STORAGE_KEY);
  return DEMO_PERSONAS.find((persona) => persona.id === selected) ?? DEMO_PERSONAS[0]!;
}

export function setActiveDemoPersona(personaId: string): void {
  if (typeof window === "undefined") return;
  const valid = DEMO_PERSONAS.some((persona) => persona.id === personaId);
  window.localStorage.setItem(DEMO_PERSONA_STORAGE_KEY, valid ? personaId : DEMO_PERSONAS[0]!.id);
}

export function restoreDemoPersona(): void {
  setActiveDemoPersona(DEMO_PERSONAS[0]!.id);
}
