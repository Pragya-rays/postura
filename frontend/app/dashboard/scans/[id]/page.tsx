"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { getScan, listDomains, listScans } from "@/lib/api";
import { ScanProgress } from "@/components/report/scan-progress";
import { ReportView } from "@/components/report/report-view";
import { formatDate } from "@/lib/utils";
import type { ScanStatus } from "@/lib/types";

const IN_PROGRESS_STATUSES = new Set<ScanStatus>(["queued", "collecting", "judging", "explaining"]);

export default function ScanReportPage({ params }: { params: { id: string } }) {
  const reportQuery = useQuery({
    queryKey: ["scan", params.id],
    queryFn: () => getScan(params.id),
    // Poll the live pipeline until it reaches a terminal state — the
    // backend commits `stages`/`status` after every stage transition
    // specifically so this polling loop sees real progress.
    refetchInterval: (query) => {
      const status = query.state.data?.scan.status;
      return status && IN_PROGRESS_STATUSES.has(status) ? 2000 : false;
    },
  });
  const domainsQuery = useQuery({ queryKey: ["domains"], queryFn: listDomains });
  const historyQuery = useQuery({ queryKey: ["scans"], queryFn: () => listScans() });

  const domain = useMemo(
    () => domainsQuery.data?.find((d) => d.hostname === reportQuery.data?.scan.hostname),
    [domainsQuery.data, reportQuery.data]
  );

  const trend = useMemo(() => {
    if (!historyQuery.data || !reportQuery.data) return [];
    return historyQuery.data
      .filter((s) => s.hostname === reportQuery.data!.scan.hostname && s.score !== undefined)
      .sort((a, b) => new Date(a.startedAt).getTime() - new Date(b.startedAt).getTime())
      .map((s) => ({ date: formatDate(s.completedAt ?? s.startedAt), score: s.score! }));
  }, [historyQuery.data, reportQuery.data]);

  if (reportQuery.isLoading || !reportQuery.data) {
    return (
      <div className="flex justify-center">
        <div className="h-8 w-8 animate-pulse rounded-full bg-cream-soft" />
      </div>
    );
  }

  const { scan, stages } = reportQuery.data;

  if (scan.status === "failed") {
    return (
      <div className="mx-auto flex max-w-lg flex-col items-center gap-3 py-16 text-center">
        <AlertTriangle className="h-8 w-8 text-status-critical" />
        <p className="font-serif text-xl text-ink">This scan failed</p>
        <p className="text-sm text-ink-secondary">
          Something went wrong partway through scanning {scan.hostname}. Start a new scan to try again.
        </p>
      </div>
    );
  }

  if (IN_PROGRESS_STATUSES.has(scan.status)) {
    return <ScanProgress stages={stages} />;
  }

  return <ReportView report={reportQuery.data} domain={domain} trend={trend} />;
}
