import Link from "next/link";
import { ArrowUpRight, RefreshCw } from "lucide-react";
import type { Domain } from "@/lib/types";
import { GradeRing } from "@/components/report/grade-ring";
import { VerificationBadge } from "./verification-badge";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";

export function DomainCard({ domain }: { domain: Domain }) {
  const scan = domain.lastScan;

  return (
    <div className="flex flex-col gap-5 rounded-xl2 border border-line bg-cream-card p-6 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-4">
        {scan?.grade && scan.score !== undefined ? (
          <GradeRing grade={scan.grade} score={scan.score} size={56} showScore={false} />
        ) : (
          <div className="flex h-14 w-14 items-center justify-center rounded-full border border-dashed border-line text-[11px] text-ink-muted">
            —
          </div>
        )}
        <div>
          <p className="font-serif text-lg text-ink">{domain.hostname}</p>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <VerificationBadge status={domain.verificationStatus} />
            {scan && (
              <span className="text-[13px] text-ink-muted">
                Last scanned {formatDate(scan.completedAt ?? scan.startedAt)}
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {scan && (
          <Link href={`/dashboard/scans/${scan.id}`}>
            <Button variant="outline" size="sm">
              View report
              <ArrowUpRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        )}
        <Link href={`/dashboard/scans/new?domainId=${domain.id}`}>
          <Button variant="ghost" size="sm">
            <RefreshCw className="h-3.5 w-3.5" />
            Re-scan
          </Button>
        </Link>
      </div>
    </div>
  );
}
