"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, Copy, KeyRound, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { verifyDomain } from "@/lib/api";
import type { Domain } from "@/lib/types";

export function VerifyBanner({ domain }: { domain: Domain }) {
  const { id: domainId, hostname, verificationToken: token } = domain;
  const [copied, setCopied] = useState<"host" | "value" | "file" | null>(null);
  const queryClient = useQueryClient();

  // Must match app/services/verification.py exactly: a TXT record at
  // `_postura-challenge.<hostname>` containing the token, or the
  // .well-known file below — either one is accepted.
  const dnsHost = `_postura-challenge.${hostname}`;
  const fileUrl = `https://${hostname}/.well-known/postura-${token}.txt`;

  const verifyMutation = useMutation({
    mutationFn: () => verifyDomain(domainId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["domains"] });
    },
  });

  function copy(value: string, which: "host" | "value" | "file") {
    navigator.clipboard?.writeText(value);
    setCopied(which);
    setTimeout(() => setCopied(null), 1500);
  }

  return (
    <div className="rounded-xl2 border border-line bg-cream-soft p-6">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-lime-soft">
          <KeyRound className="h-4.5 w-4.5 text-ink" />
        </div>
        <div>
          <h3 className="font-serif text-[17px] text-ink">Verify ownership to unlock deeper checks</h3>
          <p className="mt-1 text-sm text-ink-secondary">
            CORS misconfiguration and directory-listing checks only run on domains
            you&rsquo;ve proven you control. Do either of these:
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-line bg-cream-card p-4">
          <p className="text-[12px] font-semibold uppercase tracking-wide text-ink-muted">Option A · DNS TXT</p>
          <p className="mt-1.5 text-[13px] text-ink-secondary">Add a TXT record at this host:</p>
          <div className="mt-2 flex items-center gap-2 rounded-lg bg-forest px-3 py-2">
            <code className="flex-1 truncate font-mono text-[12px] text-forest-ink">{dnsHost}</code>
            <button onClick={() => copy(dnsHost, "host")} className="text-forest-muted hover:text-forest-ink">
              {copied === "host" ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
            </button>
          </div>
          <p className="mt-2 text-[13px] text-ink-secondary">with this value:</p>
          <div className="mt-2 flex items-center gap-2 rounded-lg bg-forest px-3 py-2">
            <code className="flex-1 truncate font-mono text-[12px] text-forest-ink">{token}</code>
            <button onClick={() => copy(token, "value")} className="text-forest-muted hover:text-forest-ink">
              {copied === "value" ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
            </button>
          </div>
        </div>

        <div className="rounded-xl border border-line bg-cream-card p-4">
          <p className="text-[12px] font-semibold uppercase tracking-wide text-ink-muted">Option B · File upload</p>
          <p className="mt-1.5 text-[13px] text-ink-secondary">Host a file at this path containing the token:</p>
          <div className="mt-2 flex items-center gap-2 rounded-lg bg-forest px-3 py-2">
            <code className="flex-1 truncate font-mono text-[12px] text-forest-ink">{fileUrl}</code>
            <button onClick={() => copy(fileUrl, "file")} className="text-forest-muted hover:text-forest-ink">
              {copied === "file" ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
            </button>
          </div>
        </div>
      </div>

      <Button
        variant="outline"
        size="sm"
        className="mt-4"
        onClick={() => verifyMutation.mutate()}
        disabled={verifyMutation.isPending}
      >
        {verifyMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
        {verifyMutation.isPending ? "Checking…" : "Check verification"}
      </Button>

      {verifyMutation.isError && (
        <p className="mt-2 text-[13px] text-status-critical">
          {verifyMutation.error instanceof Error ? verifyMutation.error.message : "Could not check verification"}
        </p>
      )}
      {verifyMutation.isSuccess && !verifyMutation.data.verified && (
        <p className="mt-2 text-[13px] text-ink-muted">
          Not verified yet — DNS and file changes can take a few minutes to propagate.
        </p>
      )}
      {verifyMutation.isSuccess && verifyMutation.data.verified && (
        <p className="mt-2 flex items-center gap-1.5 text-[13px] text-status-good">
          <Check className="h-3.5 w-3.5" />
          Verified! Re-scan to unlock the deeper checks.
        </p>
      )}
    </div>
  );
}
