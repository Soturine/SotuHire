const HTTP_PROTOCOLS = new Set(["http:", "https:"]);

export function hasExactWebHost(value: string, allowedHosts: readonly string[]): boolean {
  try {
    const parsed = new URL(value);
    const hostname = parsed.hostname.toLowerCase().replace(/\.$/, "");
    return (
      HTTP_PROTOCOLS.has(parsed.protocol) &&
      !parsed.username &&
      !parsed.password &&
      allowedHosts.some((allowed) => hostname === allowed.toLowerCase().replace(/\.$/, ""))
    );
  } catch {
    return false;
  }
}

export const isGitHubWebUrl = (value: string): boolean => hasExactWebHost(value, ["github.com"]);
