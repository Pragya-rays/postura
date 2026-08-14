import { cn } from "@/lib/utils";

export function Logo({ className, dark }: { className?: string; dark?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-3 text-[22px] font-semibold tracking-[-0.04em]", className)}>
      <svg width="32" height="32" viewBox="0 0 30 30" className="h-8 w-8 shrink-0" aria-hidden="true">
        <rect x="1" y="1" width="28" height="28" rx="8" fill="#525252" />
        <path
          d="M12 8 V22 M12 8 H17 A4 4 0 0 1 17 16 H12.5"
          fill="none"
          stroke="#ffffff"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span className={dark ? "text-white" : "text-ink"}>Postura</span>
    </span>
  );
}
