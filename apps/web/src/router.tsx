import { QueryClient } from "@tanstack/react-query";
import { createRouter } from "@tanstack/react-router";
import { routeTree } from "./routeTree.gen";

export const getRouter = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        // A local API that refuses the connection will not come back in the next seconds; one
        // retry, then the screen shows the error instead of loading for ~7 s (3 retries).
        retry: (failures, error) =>
          failures < (/Failed to fetch|NetworkError|Load failed/i.test(String(error)) ? 1 : 3),
      },
    },
  });

  const router = createRouter({
    routeTree,
    context: { queryClient },
    scrollRestoration: true,
    defaultPreloadStaleTime: 0,
  });

  return router;
};
