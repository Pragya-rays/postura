import { AlertCircle, Info, OctagonAlert, TriangleAlert } from "lucide-react";
import { cn } from "@/lib/utils";
import { SEVERITY_LABEL, type Severity } from "@/lib/types";

// Icons + text labels always ride along with the status color (never color
// alone) — see dataviz skill: status colors are a reserved, fixed palette
// with sub-3:1 contrast on light surfaces by design for warning/serious.
const CONFIG: Record<Severity, { color: string; bg: string; icon: typeof Info }> = {
  critical: { color: "#d03b3b", bg: "rgba(208,59,59,0.10)", icon: OctagonAlert },
  high: { color: "#ec835a", bg: "rgba(236,131,90,0.14)", icon: TriangleAlert },
  medium: { color: "#c98500", bg: "rgba(250,178,25,0.16)", icon: AlertCircle },
  low: { color: "#0ca30c", bg: "rgba(12,163,12,0.10)", icon: Info },
  info: { color: "#55584C", bg: "rgba(85,88,76,0.10)", icon: Info },
};

export function SeverityBadge({ severity, compact = false }: { severity: Severity; compact?: boolean }) {
  const { color, bg, icon: Icon } = CONFIG[severity];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-transparent font-medium",
        compact ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-xs"
      )}
      style={{ color, backgroundColor: bg }}
    >
      <Icon className={compact ? "h-3 w-3" : "h-3.5 w-3.5"} strokeWidth={2.25} />
      {SEVERITY_LABEL[severity]}
    </span>
  );
}
