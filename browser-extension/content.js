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
  const capture = () => {
    const visible = pageText();
    const title = firstText(["h1", "[role='heading'][aria-level='1']", "h2"]) || document.title;
    return {
      page_title: document.title,
      url: window.location.href,
      domain: window.location.hostname,
      visible_text: visible,
      job_title: title.slice(0, 500),
      company: company(),
      location: jobLocation(),
      description: visible.slice(0, 100000),
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

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message.type === "SOTUHIRE_CAPTURE") sendResponse({ capture: capture() });
    if (message.type === "SOTUHIRE_APPLICATIONS") sendResponse({ applications: applicationRows() });
    return true;
  });
})();
