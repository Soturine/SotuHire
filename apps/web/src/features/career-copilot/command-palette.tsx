import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { BriefcaseBusiness, Compass, FileSearch, FolderKanban, Search } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandShortcut,
} from "@/components/ui/command";
import { useApiMode } from "@/lib/api/mode";
import { usePreferences } from "@/lib/preferences";
import { v2Api } from "./api";

const routes = [
  { label: "Career Cockpit", route: "/dashboard", icon: Compass },
  { label: "Evidence Inbox", route: "/evidence", icon: FileSearch },
  { label: "Portfolio", route: "/portfolio", icon: FolderKanban },
  { label: "Approval Queue", route: "/approvals", icon: BriefcaseBusiness },
] as const;

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  const { mode, baseUrl } = useApiMode();
  const { locale } = usePreferences();
  const pt = locale === "pt-BR";
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((value) => !value);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);
  const results = useQuery({
    queryKey: ["v2", "search", mode, baseUrl, query],
    queryFn: () => v2Api(mode, baseUrl).search(query),
    enabled: open && query.trim().length >= 2,
  });
  const go = (route: string) => {
    setOpen(false);
    void navigate({ to: route });
  };
  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setOpen(true)}
        aria-label={pt ? "Abrir busca universal" : "Open universal search"}
      >
        <Search />
        <span className="hidden lg:inline">{pt ? "Buscar" : "Search"}</span>
        <kbd className="hidden rounded border px-1.5 text-[10px] text-muted-foreground sm:inline">
          Ctrl K
        </kbd>
      </Button>
      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput
          value={query}
          onValueChange={setQuery}
          placeholder={
            pt ? "Buscar rotas, evidências, portfólio…" : "Search routes, evidence, portfolio…"
          }
        />
        <CommandList>
          <CommandEmpty>{pt ? "Nenhum resultado." : "No results."}</CommandEmpty>
          <CommandGroup heading={pt ? "Jornada" : "Journey"}>
            {routes.map((item) => (
              <CommandItem key={item.route} onSelect={() => go(item.route)}>
                <item.icon />
                {item.label}
                <CommandShortcut>↵</CommandShortcut>
              </CommandItem>
            ))}
          </CommandGroup>
          {results.data?.length ? (
            <CommandGroup heading={pt ? "Seus dados locais" : "Your local data"}>
              {results.data.map((item) => (
                <CommandItem
                  key={`${item.entity_type}-${item.entity_id}`}
                  onSelect={() => go(item.route)}
                >
                  <FileSearch />
                  {item.title}
                  <CommandShortcut>{item.entity_type}</CommandShortcut>
                </CommandItem>
              ))}
            </CommandGroup>
          ) : null}
        </CommandList>
      </CommandDialog>
    </>
  );
}
