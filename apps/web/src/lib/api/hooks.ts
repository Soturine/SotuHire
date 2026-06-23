import { useMemo } from "react";
import { useApiMode } from "./mode";
import { makeApi } from "./client";

export function useApi() {
  const { mode, baseUrl } = useApiMode();
  return useMemo(() => makeApi(mode, baseUrl), [mode, baseUrl]);
}
