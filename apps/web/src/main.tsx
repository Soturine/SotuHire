import { RouterProvider } from "@tanstack/react-router";
import React from "react";
import ReactDOM from "react-dom/client";

import { getRouter } from "./router";
import { applyStoredAppearance } from "./lib/preferences";
import "@fontsource-variable/ibm-plex-sans";
import "@fontsource-variable/source-serif-4/opsz.css";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
import "./styles.css";

applyStoredAppearance();
const router = getRouter();

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

const root = document.getElementById("root");

if (!root) {
  throw new Error("SotuHire web root element not found.");
}

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);
