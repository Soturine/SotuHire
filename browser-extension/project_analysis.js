globalThis.SotuHireProjectAnalyzer = (() => {
  const clamp = (value) => Math.max(0, Math.min(100, Math.round(value)));
  const average = (...values) => clamp(values.reduce((sum, value) => sum + value, 0) / values.length);
  const conventional = /^(feat|fix|docs|test|refactor|perf|build|ci|chore|style)(\(.+\))?!?:\s+\S+/i;
  const generic = new Set(["update", "updates", "fix", "changes", "misc", "test", "wip", "commit"]);

  const analyze = (payload) => {
    const commits = payload.commit_messages || [];
    const goodCommits = commits.filter((message) => conventional.test(message));
    const genericCommits = commits.filter((message) => generic.has(message.trim().toLowerCase()));
    const commitScore = clamp(35 + goodCommits.length * 8 - genericCommits.length * 10);
    const readmeScore = clamp(20 + Math.min((payload.readme_text || "").length / 50, 55));
    const files = payload.files_sampled || [];
    const architectureScore = clamp(25 + files.filter((path) => /^(src|app|modules|tests|docs|\.github)\//i.test(path)).length * 8);
    const stack = [...new Set([...(payload.languages || []), ...(payload.topics || [])])];
    const technicalDepth = clamp(30 + stack.length * 8 + Math.min(files.length, 20) * 2);
    const repositoryScore = average(readmeScore, architectureScore, commitScore, technicalDepth);
    const profileScore = clamp(40 + stack.length * 8);
    const portfolioScore = average(readmeScore, repositoryScore, technicalDepth);
    const recruiterScore = average(readmeScore, commitScore, technicalDepth);
    const evidenceScore = clamp(35 + stack.length * 7 + Math.min((payload.readme_text || "").length / 100, 20));
    const overall = average(repositoryScore, portfolioScore, recruiterScore, evidenceScore);
    const grade = overall >= 85 ? "A" : overall >= 70 ? "B" : overall >= 55 ? "C" : overall >= 40 ? "D" : "F";
    const strengths = [
      ...(readmeScore >= 65 ? ["README oferece contexto util."] : []),
      ...(architectureScore >= 65 ? ["Estrutura do projeto e organizada."] : []),
      ...(commitScore >= 65 ? ["Commits comunicam mudancas com clareza."] : [])
    ];
    const weaknesses = [
      ...(readmeScore < 65 ? ["README precisa explicar melhor instalacao e uso."] : []),
      ...(architectureScore < 60 ? ["Poucos sinais arquiteturais visiveis."] : []),
      ...(commitScore < 60 ? ["Mensagens de commit podem ser mais especificas."] : [])
    ];
    const recommendations = weaknesses
      .slice(0, 5)
      .map((weakness, index) => `Prioridade ${index + 1}: ${weakness}`);
    return {
      overall_score: overall,
      grade,
      github_profile_score: profileScore,
      repository_quality_score: repositoryScore,
      portfolio_score: portfolioScore,
      project_quality_score: repositoryScore,
      recruiter_readiness_score: recruiterScore,
      documentation_score: readmeScore,
      commit_quality_score: commitScore,
      architecture_signal_score: architectureScore,
      technical_depth_score: technicalDepth,
      ats_job_evidence_score: evidenceScore,
      stack,
      summary: `${payload.title || payload.repo || "Projeto"} recebeu nota ${overall}/100 (${grade}).`,
      strengths,
      weaknesses,
      risks: weaknesses.slice(0, 4),
      priority_recommendations: recommendations,
      technical_keywords: stack,
      resume_highlights: stack.length
        ? [`Projeto ${payload.title || payload.repo || "publico"} demonstra ${stack.slice(0, 6).join(", ")}.`]
        : [],
      files_sampled: files,
      commit_analysis: {
        commit_quality_score: commitScore,
        maintenance_signal_score: clamp(40 + Math.min(commits.length, 10) * 5),
        professionalism_score: average(commitScore, clamp(50 + goodCommits.length * 5)),
        conventional_ratio: commits.length ? goodCommits.length / commits.length : 0,
        generic_messages: genericCommits,
        relevant_messages: goodCommits.slice(0, 10)
      }
    };
  };

  return { analyze };
})();
