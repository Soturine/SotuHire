import { createContext, useContext, useState, type ReactNode } from "react";

export type ApiMode = "demo" | "real";

export const DEFAULT_API_URL = "http://127.0.0.1:8787/api/v1";
const ENV_API_URL = import.meta.env.VITE_SOTUHIRE_API_URL?.trim() || DEFAULT_API_URL;

interface Ctx {
  mode: ApiMode;
  setMode: (m: ApiMode) => void;
  baseUrl: string;
  setBaseUrl: (u: string) => void;
}

const ApiModeContext = createContext<Ctx | null>(null);

export function ApiModeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ApiMode>("demo");
  const [baseUrl, setBaseUrlState] = useState<string>(ENV_API_URL);

  const setMode = (m: ApiMode) => {
    setModeState(m);
  };
  const setBaseUrl = (u: string) => {
    setBaseUrlState(u);
  };

  return (
    <ApiModeContext.Provider value={{ mode, setMode, baseUrl, setBaseUrl }}>
      {children}
    </ApiModeContext.Provider>
  );
}

export function useApiMode() {
  const ctx = useContext(ApiModeContext);
  if (!ctx) throw new Error("useApiMode must be used inside ApiModeProvider");
  return ctx;
}
