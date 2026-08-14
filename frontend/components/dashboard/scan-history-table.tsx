import Link from "next/link";
import type { ScanSummary } from "@/lib/types";
import { GradeRing } from "@/components/report/grade-ring";
import { Badge } from "@/components/ui/badge";
import { formatDateTime } from "@/lib/utils";

export function ScanHistoryTable({ scans }: { scans: ScanSummary[] }) {
  return (
    <div className="overflow-hidden rounded-xl2 border border-line bg-cream-card">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-line text-[12px] uppercase tracking-wide text-ink-muted">
              <th className="px-5 py-3 font-medium">Domain</th>
              <th className="px-5 py-3 font-medium">Tier</th>
              <th className="px-5 py-3 font-medium">Grade</th>
              <th className="px-5 py-3 font-medium">When</th>
              <th className="px-5 py-3" />
            </tr>
          </thead>
          <tbody>
            {scans.map((scan) => (
              <tr key={scan.id} className="border-b border-line last:border-0 hover:bg-cream-soft/60">
                <td className="whitespace-nowrap px-5 py-3.5 font-medium text-ink">{scan.hostname}</td>
                <td className="px-5 py-3.5">
                  <Badge variant={scan.tier === "verified" ? "accent" : "neutral"}>
                    {scan.tier === "verified" ? "Verified tier" : "Public tier"}
                  </Badge>
                </td>
                <td className="px-5 py-3.5">
                  {scan.grade && scan.score !== undefined ? (
                    <div className="flex items-center gap-2">
                      <GradeRing grade={scan.grade} score={scan.score} size={30} showScore={false} />
                      <span className="font-feature-tabular text-ink-secondary">{scan.score}/100</span>
                    </div>
                  ) : (
                    <span className="text-ink-muted">—</span>
                  )}
                </td>
                <td className="whitespace-nowrap px-5 py-3.5 text-ink-secondary">
                  {formatDateTime(scan.completedAt ?? scan.startedAt)}
                </td>
                <td className="px-5 py-3.5 text-right">
                  <Link href={`/dashboard/scans/${scan.id}`} className="text-ink-secondary hover:text-ink hover:underline">
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
