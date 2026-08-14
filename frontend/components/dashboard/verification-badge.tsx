import { CircleDashed, Clock, ShieldCheck } from "lucide-react";
import type { VerificationStatus } from "@/lib/types";

const CONFIG: Record<VerificationStatus, { label: string; color: string; bg: string; icon: typeof ShieldCheck }> = {
  verified: { label: "Verified", color: "#0ca30c", bg: "rgba(12,163,12,0.10)", icon: ShieldCheck },
  pending: { label: "Verification pending", color: "#c98500", bg: "rgba(250,178,25,0.16)", icon: Clock },
  unverified: { label: "Unverified", color: "#55584C", bg: "rgba(85,88,76,0.10)", icon: CircleDashed },
};

export function VerificationBadge({ status }: { status: VerificationStatus }) {
  const { label, color, bg, icon: Icon } = CONFIG[status];
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
      style={{ color, backgroundColor: bg }}
    >
      <Icon className="h-3.5 w-3.5" strokeWidth={2.25} />
      {label}
    </span>
  );
}
