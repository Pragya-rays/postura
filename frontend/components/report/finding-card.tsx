"use client";

import { useState } from "react";
import { ChevronDown, Wrench } from "lucide-react";
import type { Finding } from "@/lib/types";
import { SeverityBadge } from "./severity-badge";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function FindingCard({ finding, technical }: { finding: Finding; technical: boolean }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-xl2 border border-line bg-cream-card p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[12px] font-medium uppercase tracking-wide text-ink-muted">{finding.category}</p>
          <h3 className="mt-1 font-serif text-[18px] text-ink">{finding.title}</h3>
        </div>
        <SeverityBadge severity={finding.severity} />
      </div>

      <p className="mt-3.5 text-[15px] leading-relaxed text-ink-secondary">
        {technical ? finding.technicalExplanation : finding.simpleExplanation}
      </p>

      {technical && (
        <div className="mt-4 flex flex-wrap gap-2">
          <Badge variant="outline" className="font-feature-tabular">
            {finding.cvssVector} · {finding.cvssScore.toFixed(1)}
          </Badge>
          <Badge variant="outline">{finding.owaspCategory}</Badge>
          {finding.fromCache && <Badge variant="outline">Cached explanation</Badge>}
        </div>
      )}

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="mt-4 inline-flex items-center gap-1.5 text-[13px] font-medium text-ink hover:underline"
      >
        <Wrench className="h-3.5 w-3.5" />
        Show me how
        <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div className="mt-3 space-y-2 rounded-xl bg-cream-soft p-4">
          <ol className="space-y-2">
            {finding.remediation.map((step, i) => (
              <li key={i} className="flex gap-2.5 text-[14px] leading-snug text-ink-secondary">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-ink/10 text-[11px] font-semibold text-ink">
                  {i + 1}
                </span>
                <span dangerouslySetInnerHTML={{ __html: mdCode(step) }} />
              </li>
            ))}
          </ol>

          {technical && (
            <div className="mt-3 border-t border-line pt-3">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Evidence</p>
              <pre className="mt-1.5 overflow-x-auto rounded-lg bg-forest p-3 text-[12px] text-forest-ink">
                {JSON.stringify(finding.evidence, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Minimal inline-code renderer for `backtick` spans in remediation copy —
// avoids pulling in a markdown dependency for a handful of code snippets.
function mdCode(text: string): string {
  return text.replace(
    /`([^`]+)`/g,
    '<code class="rounded bg-ink/10 px-1.5 py-0.5 font-mono text-[12.5px] text-ink">$1</code>'
  );
}
