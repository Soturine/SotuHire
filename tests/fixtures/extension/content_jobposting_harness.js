const fs = require("fs");
const path = require("path");
const vm = require("vm");

const posting = {
  "@context": "https://schema.org",
  "@type": "https://schema.org/JobPosting",
  title: "Pessoa Desenvolvedora Backend",
  description: "<p>Construa APIs <strong>Python</strong>.</p>",
  hiringOrganization: {
    "@type": "Organization",
    name: "Empresa Exemplo",
  },
  jobLocation: {
    "@type": "Place",
    address: {
      "@type": "PostalAddress",
      addressLocality: "Recife",
      addressRegion: "PE",
      addressCountry: { "@type": "Country", name: "Brasil" },
    },
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  mainEntity: { list: [{ "@type": "Thing" }, posting] },
};

const body = { innerText: "Texto genérico visível da página" };
let listener;

global.window = {
  location: {
    href: "https://jobs.example/vaga/42?utm_source=test",
    hostname: "jobs.example",
    pathname: "/vaga/42",
  },
};
global.document = {
  title: "Título genérico",
  body,
  querySelector: () => null,
  querySelectorAll: (selector) => {
    if (selector === "main, article, [role='main']") return [body];
    if (selector === "script[type='application/ld+json']") {
      return [{ textContent: JSON.stringify(jsonLd) }];
    }
    return [];
  },
  createElement: () => {
    const node = { innerText: "" };
    Object.defineProperty(node, "innerHTML", {
      set(value) {
        node.innerText = String(value)
          .replace(/<[^>]+>/g, " ")
          .replace(/\s+/g, " ")
          .trim();
      },
    });
    return node;
  },
};
global.chrome = {
  runtime: {
    onMessage: {
      addListener(callback) {
        listener = callback;
      },
    },
  },
};

const source = fs.readFileSync(
  path.resolve(process.argv[2], "content.js"),
  "utf8",
);
vm.runInThisContext(source, { filename: "content.js" });

let response;
listener({ type: "SOTUHIRE_CAPTURE" }, {}, (payload) => {
  response = payload;
});
process.stdout.write(JSON.stringify(response.capture));
