"use client";

import { Suspense, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowRight, Globe2, ShieldCheck, Sparkles } from "lucide-react";
import { addDomain, ApiError, listDomains, startScan } from "@/lib/api";
import { validateTarget } from "@/lib/validate-target";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { VerificationBadge } from "@/components/dashboard/verification-badge";
import { cn } from "@/lib/utils";

function NewScanForm() {
  const router = useRouter();
  const params = useSearchParams();
  const preselectDomainId = params.get("domainId");
  const prefillHostname = params.get("domain") ?? "";

  const domainsQuery = useQuery({ queryKey: ["domains"], queryFn: listDomains });
  const [selectedId, setSelectedId] = useState<string | null>(preselectDomainId);
  const [newHostname, setNewHostname] = useState(prefillHostname);
  // `upgrade: true` when the backend returned 402 (a Free-tier plan limit) —
  // rendered as an "upgrade to unlock" prompt instead of a plain error.
  const [error, setError] = useState<{ message: string; upgrade: boolean } | null>(null);

  const selectedDomain = useMemo(
    () => domainsQuery.data?.find((d) => d.id === selectedId) ?? null,
    [domainsQuery.data, selectedId]
  );

  const scanMutation = useMutation({
    mutationFn: async () => {
      let domainId = selectedId;
      if (!domainId) {
        const check = validateTarget(newHostname);
        if (!check.ok) throw new Error(check.reason);
        const created = await addDomain(check.hostname);
        domainId = created.id;
      }
      return startScan(domainId);
    },
    onSuccess: (scan) => router.push(`/dashboard/scans/${scan.id}`),
    onError: (e: Error) => setError({ message: e.message, upgrade: e instanceof ApiError && e.status === 402 }),
  });

  const tier = selectedDomain?.verificationStatus === "verified" ? "verified" : "public";

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="font-serif text-[28px] text-ink">New scan</h1>
      <p className="mt-1 text-sm text-ink-secondary">
        Pick a domain you&rsquo;ve already added, or scan a new one.
      </p>

      {domainsQuery.data && domainsQuery.data.length > 0 && (
        <div className="mt-7">
          <p className="mb-2.5 text-[13px] font-medium text-ink-secondary">Existing domains</p>
          <div className="space-y-2">
            {domainsQuery.data.map((d) => (
              <button
                key={d.id}
                type="button"
                onClick={() => {
                  setSelectedId(d.id);
                  setNewHostname("");
                  setError(null);
                }}
                className={cn(
                  "flex w-full items-center justify-between rounded-xl border px-4 py-3 text-left transition-colors",
                  selectedId === d.id ? "border-ink bg-ink/5" : "border-line bg-cream-card hover:bg-cream-soft/60"
                )}
              >
                <span className="flex items-center gap-2.5 text-sm font-medium text-ink">
                  <Globe2 className="h-4 w-4 text-ink-muted" />
                  {d.hostname}
                </span>
                <VerificationBadge status={d.verificationStatus} />
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="mt-7">
        <p className="mb-2.5 text-[13px] font-medium text-ink-secondary">Or scan a new domain</p>
        <Input
          value={newHostname}
          onChange={(e) => {
            setNewHostname(e.target.value);
            setSelectedId(null);
            setError(null);
          }}
          placeholder="yourcompany.com"
        />
      </div>

      <div className="mt-6 flex items-start gap-3 rounded-xl border border-line bg-cream-soft p-4">
        <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-ink-muted" />
        <p className="text-[13px] leading-relaxed text-ink-secondary">
          {tier === "verified"
            ? "This domain is verified — the scan will include CORS and directory-listing checks."
            : "This will run the public tier: TLS, headers, cookies, DNS/email auth, WHOIS, robots.txt, and tech fingerprint. Verify ownership afterward to unlock CORS and directory-listing checks."}
        </p>
      </div>

      {error && error.upgrade && (
        <div className="mt-4 flex items-start gap-3 rounded-lg bg-ink/5 px-3.5 py-3 text-sm text-ink">
          <Sparkles className="mt-0.5 h-4 w-4 shrink-0" />
          <div>
            <p>{error.message}</p>
            <Link href="/dashboard/billing" className="mt-1 inline-block font-medium underline">
              Upgrade to Pro
            </Link>
          </div>
        </div>
      )}
      {error && !error.upgrade && (
        <div className="mt-4 flex items-center gap-2 rounded-lg bg-status-critical/10 px-3.5 py-2.5 text-sm text-status-critical">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error.message}
        </div>
      )}

      <Button
        className="mt-7 w-full"
        size="lg"
        variant="accent"
        disabled={scanMutation.isPending || (!selectedId && !newHostname.trim())}
        onClick={() => {
          setError(null);
          scanMutation.mutate();
        }}
      >
        {scanMutation.isPending ? "Starting scan…" : "Start scan"}
        {!scanMutation.isPending && <ArrowRight className="h-4 w-4" />}
      </Button>
    </div>
  );
}

export default function NewScanPage() {
  return (
    <Suspense>
      <NewScanForm />
    </Suspense>
  );
}
