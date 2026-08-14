"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Plus, ShieldOff } from "lucide-react";
import { listDomains, listScans } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { DomainCard } from "@/components/dashboard/domain-card";
import { ScanHistoryTable } from "@/components/dashboard/scan-history-table";

export default function DashboardPage() {
  const domainsQuery = useQuery({ queryKey: ["domains"], queryFn: listDomains });
  const scansQuery = useQuery({ queryKey: ["scans"], queryFn: () => listScans() });

  return (
    <div className="space-y-12">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-serif text-[28px] text-ink">Your domains</h1>
          <p className="mt-1 text-sm text-ink-secondary">Track posture over time, one domain at a time.</p>
        </div>
        <Link href="/dashboard/scans/new">
          <Button variant="primary">
            <Plus className="h-4 w-4" />
            Add domain
          </Button>
        </Link>
      </div>

      {domainsQuery.isLoading && (
        <div className="grid gap-4 sm:grid-cols-2">
          {[0, 1].map((i) => (
            <div key={i} className="h-24 animate-pulse rounded-xl2 border border-line bg-cream-soft" />
          ))}
        </div>
      )}

      {domainsQuery.data && domainsQuery.data.length === 0 && (
        <div className="flex flex-col items-center rounded-xl2 border border-dashed border-line py-16 text-center">
          <ShieldOff className="h-8 w-8 text-ink-muted" />
          <p className="mt-4 font-serif text-lg text-ink">No domains yet</p>
          <p className="mt-1 max-w-sm text-sm text-ink-secondary">
            Add your first domain to get a grade, a plain-English summary, and
            ranked fixes in under 90 seconds.
          </p>
          <Link href="/dashboard/scans/new" className="mt-5">
            <Button variant="accent">
              <Plus className="h-4 w-4" />
              Add your first domain
            </Button>
          </Link>
        </div>
      )}

      {domainsQuery.data && domainsQuery.data.length > 0 && (
        <div className="space-y-4">
          {domainsQuery.data.map((domain) => (
            <DomainCard key={domain.id} domain={domain} />
          ))}
        </div>
      )}

      <div>
        <h2 className="font-serif text-xl text-ink">Scan history</h2>
        <p className="mt-1 text-sm text-ink-secondary">Every scan, kept — even after logout.</p>
        <div className="mt-5">
          {scansQuery.data && <ScanHistoryTable scans={scansQuery.data} />}
        </div>
      </div>
    </div>
  );
}
