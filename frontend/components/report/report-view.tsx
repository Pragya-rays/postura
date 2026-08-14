"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { RefreshCw } from "lucide-react";
import type { Domain, ScanReport } from "@/lib/types";
import { SEVERITY_ORDER } from "@/lib/types";
import { GradeRing } from "./grade-ring";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TopFixes } from "./top-fixes";
import { SeverityChart } from "./severity-chart";
import { GradeTrendChart } from "./grade-trend-chart";
import { FindingCard } from "./finding-card";
import { VerifyBanner } from "./verify-banner";
import { formatDateTime } from "@/lib/utils";

export function ReportView({
  report,
  domain,
  trend,
}: {
  report: ScanReport;
  domain?: Domain;
  trend: { date: string; score: number }[];
}) {
  const router = useRouter();
  const [technical, setTechnical] = useState(false);
  const { scan, summary, findings, severityBreakdown } = report;

  const sortedFindings = useMemo(
    () =>
      [...findings].sort((a, b) => SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity)),
    [findings]
  );
  const topThree = sortedFindings.slice(0, 3);

  return (
    <div className="space-y-10">
      <div className="rounded-xl2 border border-line bg-cream-card p-7">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="flex items-start gap-5">
            {scan.grade && scan.score !== undefined && <GradeRing grade={scan.grade} score={scan.score} size={80} />}
            <div>
              <div className="flex items-center gap-2">
                <p className="font-serif text-2xl text-ink">{scan.hostname}</p>
                <Badge variant={scan.tier === "verified" ? "accent" : "neutral"}>
                  {scan.tier === "verified" ? "Verified tier" : "Public tier"}
                </Badge>
              </div>
              <p className="mt-1 text-[13px] text-ink-muted">
                Scanned {formatDateTime(scan.completedAt ?? scan.startedAt)}
              </p>
              <p className="mt-3 max-w-lg text-[15px] leading-relaxed text-ink-secondary">{summary}</p>
            </div>
          </div>

          <div className="flex flex-col items-end gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                router.push(domain ? `/dashboard/scans/new?domainId=${domain.id}` : "/dashboard/scans/new")
              }
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Re-scan
            </Button>
            <div className="w-40">
              <GradeTrendChart points={trend} />
            </div>
          </div>
        </div>
      </div>

      {domain && domain.verificationStatus !== "verified" && <VerifyBanner domain={domain} />}

      <TopFixes findings={topThree} />

      <div className="flex flex-col gap-8 lg:flex-row">
        <div className="flex-1 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-serif text-xl text-ink">All findings ({sortedFindings.length})</h2>
            <div className="flex items-center gap-3 rounded-full border border-line bg-cream-card px-3.5 py-2">
              <span className={technical ? "text-[13px] text-ink-muted" : "text-[13px] font-medium text-ink"}>
                Simple
              </span>
              <Switch checked={technical} onCheckedChange={setTechnical} aria-label="Toggle technical detail" />
              <span className={technical ? "text-[13px] font-medium text-ink" : "text-[13px] text-ink-muted"}>
                Technical
              </span>
            </div>
          </div>

          <div className="space-y-4">
            {sortedFindings.map((f) => (
              <div key={f.id} id={f.id}>
                <FindingCard finding={f} technical={technical} />
              </div>
            ))}
          </div>
        </div>

        <div className="w-full shrink-0 lg:w-72">
          <div className="rounded-xl2 border border-line bg-cream-card p-6">
            <h3 className="font-serif text-[17px] text-ink">Severity breakdown</h3>
            <div className="mt-4">
              <SeverityChart breakdown={severityBreakdown} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
