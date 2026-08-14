import { AlertTriangle, Check, Loader2 } from "lucide-react";
import type { ScanStage } from "@/lib/types";
import { cn } from "@/lib/utils";

// Purely presentational — driven by real `stages` from GET /scans/:id
// (polled by the parent page), not a simulated timer. Each stage already
// carries its own status (pending/active/done/error) straight from the
// backend pipeline, so this just renders what's there.
export function ScanProgress({ stages }: { stages: ScanStage[] }) {
  return (
    <div className="mx-auto max-w-lg py-16">
      <p className="text-center text-[12px] font-semibold uppercase tracking-wide text-ink-muted">Scanning</p>
      <h1 className="mt-2 text-center font-serif text-2xl text-ink">
        Running Collect → Judge → Explain → Present
      </h1>

      <div className="mt-10 space-y-3">
        {stages.map((stage) => (
          <div
            key={stage.key}
            className={cn(
              "flex items-center gap-3.5 rounded-xl border px-4 py-3.5 transition-colors",
              stage.status === "done" && "border-line bg-cream-card",
              stage.status === "active" && "border-ink/25 bg-cream-card shadow-card",
              stage.status === "error" && "border-status-critical/30 bg-status-critical/5",
              stage.status === "pending" && "border-line bg-transparent opacity-50"
            )}
          >
            <div
              className={cn(
                "flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
                stage.status === "done" && "bg-lime",
                stage.status === "active" && "bg-ink/10",
                stage.status === "error" && "bg-status-critical/15",
                stage.status === "pending" && "bg-line"
              )}
            >
              {stage.status === "done" && <Check className="h-3.5 w-3.5 text-ink" strokeWidth={3} />}
              {stage.status === "active" && <Loader2 className="h-3.5 w-3.5 animate-spin text-ink" />}
              {stage.status === "error" && <AlertTriangle className="h-3.5 w-3.5 text-status-critical" />}
            </div>
            <div>
              <p className="text-sm font-medium text-ink">{stage.label}</p>
              {stage.detail && <p className="text-[12px] text-ink-muted">{stage.detail}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
