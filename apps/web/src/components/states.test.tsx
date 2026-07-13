import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EmptyState, ErrorState, LoadingState } from "./states";

describe("shared states", () => {
  it("renders an accessible loading label", () => {
    render(<LoadingState label="Carregando backups" />);

    expect(screen.getByText("Carregando backups")).toBeInTheDocument();
  });

  it("shows the error and retries only after user action", () => {
    const retry = vi.fn();
    render(<ErrorState error={new Error("API local indisponível")} onRetry={retry} />);

    expect(screen.getByText("API local indisponível")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(retry).toHaveBeenCalledOnce();
  });

  it("renders empty-state guidance and its action", () => {
    render(
      <EmptyState
        title="Nenhum backup"
        description="Crie o primeiro backup local."
        action={<button type="button">Criar backup</button>}
      />,
    );

    expect(screen.getByText("Nenhum backup")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Criar backup" })).toBeEnabled();
  });
});
