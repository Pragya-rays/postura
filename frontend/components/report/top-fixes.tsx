import type { Finding } from "@/lib/types";
import { SeverityBadge } from "./severity-badge";

export function TopFixes({ findings }: { findings: Finding[] }) {
  return (
    <div>
      <h2 className="font-serif text-xl text-ink">Fix these first</h2>
      <p className="mt-1 text-sm text-ink-secondary">Ranked by severity — the three that matter most right now.</p>

      <div className="mt-5 grid gap-4 sm:grid-cols-3">
        {findings.map((f, i) => (
          <a
            key={f.id}
            href={`#${f.id}`}
            className="group flex flex-col rounded-xl2 border border-line bg-cream-card p-5 transition-shadow hover:shadow-card"
          >
            <div className="flex items-center justify-between">
              <span className="font-serif text-2xl text-ink-muted">{i + 1}</span>
              <SeverityBadge severity={f.severity} compact />
            </div>
            <h3 className="mt-3 font-serif text-[16px] leading-snug text-ink">{f.title}</h3>
            <p className="mt-2 line-clamp-3 text-[13.5px] leading-relaxed text-ink-secondary">
              {f.simpleExplanation}
            </p>
            <span className="mt-3 text-[13px] font-medium text-ink underline-offset-2 group-hover:underline">
              Show me how →
            </span>
          </a>
        ))}
      </div>
    </div>
  );
}
