(() => {
  const text = (element) => (element?.innerText || "").replace(/\s+/g, " ").trim();
  const firstText = (selectors) => {
    for (const selector of selectors) {
      const value = text(document.querySelector(selector));
      if (value) return value;
    }
    return "";
  };
  const pageText = () => {
    const candidates = [...document.querySelectorAll("main, article, [role='main']")];
    const preferred = candidates.map(text).sort((a, b) => b.length - a.length)[0];
    return (preferred || text(document.body)).slice(0, 200000);
  };
  const company = () =>
    firstText([
      "[data-company-name]",
      ".company-name",
      ".job-details-jobs-unified-top-card__company-name",
      "[class*='company']"
    ]).slice(0, 500);
  const jobLocation = () =>
    firstText([
      "[data-location]",
      ".job-location",
      ".job-details-jobs-unified-top-card__primary-description-container",
      "[class*='location']"
    ]).slice(0, 500);
  const stripHtml = (value) => {
    const node = document.createElement("div");
    node.innerHTML = String(value || "");
    return text(node);
  };
  const jobPostingFromValue = (value) => {
    if (Array.isArray(value)) {
      for (const item of value) {
        const found = jobPostingFromValue(item);
        if (found) return found;
      }
      return null;
    }
    if (!value || typeof value !== "object") return null;
    const types = Array.isArray(value["@type"])
      ? value["@type"]
      : [value["@type"]];
    if (
      types.some(
        (type) =>
          String(type).toLowerCase().split(/[\/#]/).pop() === "jobposting",
      )
    ) {
      return value;
    }
    for (const nested of Object.values(value)) {
      const found = jobPostingFromValue(nested);
      if (found) return found;
    }
    return null;
  };
  const structuredJobPosting = () => {
    for (const script of document.querySelectorAll("script[type='application/ld+json']")) {
      try {
        const found = jobPostingFromValue(JSON.parse(script.textContent || "null"));
        if (found) return found;
      } catch (_error) {
        // Invalid JSON-LD is ignored; semantic and visible-text fallbacks remain available.
      }
    }
    return null;
  };
  const structuredCompany = (posting) => {
    const organization = posting?.hiringOrganization;
    return typeof organization === "string"
      ? organization
      : String(organization?.name || "");
  };
  const structuredLocation = (posting) => {
    const locations = Array.isArray(posting?.jobLocation)
      ? posting.jobLocation
      : [posting?.jobLocation];
    const values = locations
      .map((item) => item?.address || item)
      .filter(Boolean)
      .map((address) => {
        if (typeof address === "string") return address;
        const country =
          typeof address.addressCountry === "string"
            ? address.addressCountry
            : address.addressCountry?.name;
        return [
          address.addressLocality,
          address.addressRegion,
          country,
        ]
          .filter(Boolean)
          .join(", ");
      })
      .filter(Boolean);
    if (values.length) return values.join(" · ");
    return String(posting?.jobLocationType || "");
  };
  const capture = () => {
    const visible = pageText();
    const posting = structuredJobPosting();
    const structuredDescription = stripHtml(posting?.description || "");
    const title =
      String(posting?.title || posting?.name || "").trim() ||
      firstText(["h1", "[role='heading'][aria-level='1']", "h2"]) ||
      document.title;
    return {
      kind: "job",
      page_title: document.title,
      url: window.location.href,
      domain: window.location.hostname,
      visible_text: visible,
      job_title: title.slice(0, 500),
      company: structuredCompany(posting).slice(0, 500) || company(),
      location: structuredLocation(posting).slice(0, 500) || jobLocation(),
      description: (structuredDescription || visible).slice(0, 100000),
      extraction_strategy: posting ? "schema_org_jobposting" : "semantic_visible_text",
      structured_data: posting || {},
      captured_at: new Date().toISOString(),
      collection_method: "browser_assisted_capture"
    };
  };
  const applicationRows = () => {
    const selectors = [
      "[data-job-id]",
      "[data-testid*='job']",
      "[data-testid*='vaga']",
      "li.jobs-job-tracker-list-item",
      "[class*='job-tracker'] li",
      "[class*='application'] li",
      "[class*='job-card']",
      "[class*='vacancy']",
      "[class*='vaga']",
      "[class*='opportunity']"
    ];
    const rows = [...document.querySelectorAll(selectors.join(","))];
    const seen = new Set();
    return rows
      .map((row) => {
        const rowText = text(row);
        const anchor = row.querySelector("a[href]");
        const title = text(row.querySelector("h1,h2,h3,[class*='title'],[data-testid*='title']")) || text(anchor);
        const rowCompany = text(row.querySelector("[class*='company'],[class*='employer'],[data-testid*='company']"));
        const rowLocation = text(row.querySelector("[class*='location'],[data-testid*='location']"));
        const url = anchor?.href || window.location.href;
        return {
          kind: "job",
          page_title: title || document.title,
          url,
          domain: new URL(url).hostname,
          visible_text: rowText,
          job_title: title,
          company: rowCompany,
          location: rowLocation,
          description: rowText,
          captured_at: new Date().toISOString(),
          collection_method: "browser_assisted_capture"
        };
      })
      .filter((item) => {
        const key = `${item.job_title}|${item.company}|${item.url}`;
        if (!item.job_title || seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .slice(0, 500);
  };
  const projectCapture = (deep = false) => {
    const parts = window.location.pathname.split("/").filter(Boolean);
    const github = window.location.hostname.toLowerCase() === "github.com";
    const pageType = github
      ? (parts.length >= 2 ? "github_repo" : "github_profile")
      : "portfolio";
    const links = [...document.querySelectorAll("a[href]")];
    const files = links
      .map((anchor) => anchor.getAttribute("title") || anchor.getAttribute("href") || "")
      .filter((value) => /(^|\/)(README|src|app|modules|tests|docs|\.github|package\.json|pyproject\.toml|requirements\.txt|Dockerfile)/i.test(value))
      .slice(0, deep ? 200 : 80);
    const commitMessages = [...document.querySelectorAll(
      "[data-testid*='commit'] a, [class*='commit'] a, a[href*='/commit/']"
    )].map(text).filter(Boolean).slice(0, deep ? 200 : 30);
    const topics = [...document.querySelectorAll("[data-octo-click*='topic'], [class*='topic']")]
      .map(text).filter(Boolean).slice(0, 100);
    const languages = [...document.querySelectorAll("[aria-label*='language'], [class*='language']")]
      .map(text).filter(Boolean).slice(0, 100);
    const readme = firstText([
      "#readme",
      "article.markdown-body",
      "[data-testid='readme']",
      "[class*='readme']"
    ]);
    return {
      url: window.location.href,
      owner: github ? (parts[0] || "") : "",
      repo: github ? (parts[1] || "") : "",
      title: firstText(["h1", "title"]) || document.title,
      page_type: pageType,
      visible_text: pageText(),
      readme_text: readme.slice(0, 100000),
      files_sampled: [...new Set(files)],
      commit_messages: [...new Set(commitMessages)],
      languages: [...new Set(languages)],
      topics: [...new Set(topics)],
      analysis_result: { use_github_api: pageType === "github_repo" },
      provider_used: "local"
    };
  };

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message.type === "SOTUHIRE_CAPTURE") sendResponse({ capture: capture() });
    if (message.type === "SOTUHIRE_APPLICATIONS") sendResponse({ applications: applicationRows() });
    if (message.type === "SOTUHIRE_PROJECT") {
      sendResponse({ project: projectCapture(Boolean(message.deep)) });
    }
    return true;
  });
})();
