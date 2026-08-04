import { Check, ClipboardCopy, Download, Pencil, RefreshCw, RotateCcw, X } from "lucide-react";
import { useState } from "react";
import type { ApplicationKit, ApplicationKitItem } from "@/lib/api/types";
import { toast } from "@/lib/notify";
import { cn } from "@/lib/utils";

const STATUS_LABEL: Record<ApplicationKitItem["status"], string> = {
  pending: "Pendente",
  accepted: "Aceito",
  edited: "Editado",
  rejected: "Rejeitado",
  stale: "Desatualizado",
};

export function ApplicationKitReview({
  kit,
  demo,
  pending,
  onRegenerate,
  onExport,
  onReview,
}: {
  kit: ApplicationKit;
  demo: boolean;
  pending: boolean;
  onRegenerate: () => void;
  onExport: () => void;
  onReview: (
    item: ApplicationKitItem,
    status: ApplicationKitItem["status"],
    editedContent?: string,
  ) => void;
}) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const approved = kit.items.filter(
    (item) => item.status === "accepted" || item.status === "edited",
  );

  async function copy(text: string, label: string): Promise<void> {
    await navigator.clipboard.writeText(text);
    toast.success(`${label} copiado. Revise antes de enviar.`);
  }

  return (
    <div className="space-y-4" data-testid="application-kit-review">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs text-muted-foreground">
            {kit.items.length} item(ns) · {approved.length} pronto(s) para copiar/exportar
          </p>
          {kit.stale_reason && (
            <p className="mt-1 text-xs text-warning-foreground">
              Desatualizado: {kit.stale_reason}
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() =>
              copy(
                approved
                  .map((item) => `${item.type}\n${item.edited_content || item.content}`)
                  .join("\n\n"),
                "Kit aprovado",
              )
            }
            disabled={!approved.length || pending}
            className="inline-flex items-center gap-1.5 rounded-md border px-3 py-2 text-xs font-semibold hover:bg-muted disabled:opacity-40"
          >
            <ClipboardCopy className="h-3.5 w-3.5" /> Copiar aprovados
          </button>
          <button
            type="button"
            onClick={onExport}
            disabled={!approved.length || pending}
            className="inline-flex items-center gap-1.5 rounded-md border px-3 py-2 text-xs font-semibold hover:bg-muted disabled:opacity-40"
          >
            <Download className="h-3.5 w-3.5" /> Exportar
          </button>
          <button
            type="button"
            onClick={onRegenerate}
            disabled={pending}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground disabled:opacity-40"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", pending && "animate-spin")} /> Regenerar
          </button>
        </div>
      </div>

      {demo && (
        <p className="rounded-lg border border-warning/30 bg-warning/10 p-3 text-xs">
          <strong>DEMO:</strong> decisões e textos são fictícios; nenhum dado real é alterado.
        </p>
      )}

      <div className="grid gap-3 lg:grid-cols-2">
        {kit.items.map((item) => {
          const editing = editingId === item.item_id;
          const displayContent = item.edited_content || item.content;
          const copyable = item.status === "accepted" || item.status === "edited";
          return (
            <article key={item.item_id} className="rounded-xl border bg-background p-4">
              <div className="flex items-center justify-between gap-2">
                <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                  {item.type.replaceAll("_", " ")}
                </p>
                <span
                  className={cn(
                    "rounded-full px-2 py-1 text-[10px] font-bold uppercase",
                    item.status === "accepted" && "bg-success/15 text-success",
                    item.status === "edited" && "bg-accent/15 text-accent",
                    item.status === "rejected" && "bg-destructive/10 text-destructive",
                    (item.status === "pending" || item.status === "stale") &&
                      "bg-warning/15 text-warning-foreground",
                  )}
                >
                  {STATUS_LABEL[item.status]}
                </span>
              </div>

              {editing ? (
                <textarea
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  className="mt-3 min-h-36 w-full rounded-lg border bg-background p-3 text-sm leading-6"
                  aria-label={`Editar ${item.type}`}
                />
              ) : (
                <p className="mt-3 whitespace-pre-wrap text-sm leading-6">{displayContent}</p>
              )}

              <p className="mt-3 text-xs text-muted-foreground">
                {item.evidence_used.length} evidência(s) · {item.warnings.length} aviso(s)
              </p>
              {item.warnings.map((warning) => (
                <p key={warning} className="mt-1 text-xs text-warning-foreground">
                  {warning}
                </p>
              ))}

              <div className="mt-4 flex flex-wrap gap-2 border-t pt-3">
                {editing ? (
                  <>
                    <button
                      type="button"
                      onClick={() => {
                        onReview(item, "edited", draft);
                        setEditingId(null);
                      }}
                      disabled={!draft.trim() || pending}
                      className="inline-flex items-center gap-1 rounded-md bg-primary px-2.5 py-1.5 text-xs font-semibold text-primary-foreground disabled:opacity-40"
                    >
                      <Check className="h-3.5 w-3.5" /> Salvar edição
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingId(null)}
                      className="rounded-md border px-2.5 py-1.5 text-xs"
                    >
                      Cancelar
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      type="button"
                      onClick={() => onReview(item, "accepted")}
                      disabled={pending || item.status === "accepted"}
                      className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs hover:bg-muted disabled:opacity-40"
                    >
                      <Check className="h-3.5 w-3.5" /> Aceitar
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setEditingId(item.item_id);
                        setDraft(displayContent);
                      }}
                      disabled={pending}
                      className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs hover:bg-muted disabled:opacity-40"
                    >
                      <Pencil className="h-3.5 w-3.5" /> Editar
                    </button>
                    <button
                      type="button"
                      onClick={() => onReview(item, "rejected")}
                      disabled={pending || item.status === "rejected"}
                      className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs hover:bg-muted disabled:opacity-40"
                    >
                      <X className="h-3.5 w-3.5" /> Rejeitar
                    </button>
                    {item.status !== "pending" && (
                      <button
                        type="button"
                        onClick={() => onReview(item, "pending")}
                        disabled={pending}
                        className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs hover:bg-muted disabled:opacity-40"
                      >
                        <RotateCcw className="h-3.5 w-3.5" /> Desfazer
                      </button>
                    )}
                    {copyable && (
                      <button
                        type="button"
                        onClick={() => copy(displayContent, item.type.replaceAll("_", " "))}
                        className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs hover:bg-muted"
                      >
                        <ClipboardCopy className="h-3.5 w-3.5" /> Copiar
                      </button>
                    )}
                  </>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
