"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertTriangle, Check, CheckCircle2, Sparkles } from "lucide-react";
import { createCheckoutSession, createPortalSession, getSubscription } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";

const PRO_FEATURES = [
  "Up to 10 domains",
  "Unlimited scans (fair-use capped)",
  "Simple + Technical report mode (CVSS, OWASP, raw evidence)",
];

function BillingContent() {
  const params = useSearchParams();
  const checkoutResult = params.get("checkout"); // "success" | "cancelled" | null
  const [error, setError] = useState<string | null>(null);

  const subscriptionQuery = useQuery({ queryKey: ["billing"], queryFn: getSubscription });

  const checkoutMutation = useMutation({
    mutationFn: createCheckoutSession,
    onSuccess: ({ url }) => {
      window.location.href = url;
    },
    onError: (e: Error) => setError(e.message),
  });

  const portalMutation = useMutation({
    mutationFn: createPortalSession,
    onSuccess: ({ url }) => {
      window.location.href = url;
    },
    onError: (e: Error) => setError(e.message),
  });

  if (subscriptionQuery.isLoading || !subscriptionQuery.data) {
    return (
      <div className="flex justify-center">
        <div className="h-8 w-8 animate-pulse rounded-full bg-cream-soft" />
      </div>
    );
  }

  const subscription = subscriptionQuery.data;
  const isPro = subscription.tier === "pro";

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="font-serif text-[28px] text-ink">Billing</h1>
      <p className="mt-1 text-sm text-ink-secondary">Manage your plan and payment details.</p>

      {checkoutResult === "success" && (
        <div className="mt-6 flex items-center gap-2 rounded-lg bg-status-good/10 px-3.5 py-2.5 text-sm text-status-good">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          You&rsquo;re on Pro now — thanks for upgrading.
        </div>
      )}
      {checkoutResult === "cancelled" && (
        <div className="mt-6 flex items-center gap-2 rounded-lg bg-cream-soft px-3.5 py-2.5 text-sm text-ink-secondary">
          Checkout was cancelled — you&rsquo;re still on the Free plan.
        </div>
      )}
      {error && (
        <div className="mt-6 flex items-center gap-2 rounded-lg bg-status-critical/10 px-3.5 py-2.5 text-sm text-status-critical">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      <div className="mt-7 rounded-xl2 border border-line bg-cream-card p-7">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isPro && <Sparkles className="h-4 w-4 text-ink" />}
            <p className="font-serif text-xl text-ink">{isPro ? "Pro" : "Free"} plan</p>
          </div>
        </div>

        {isPro ? (
          <>
            <p className="mt-2 text-sm text-ink-secondary">
              {subscription.cancelAtPeriodEnd && subscription.currentPeriodEnd
                ? `Cancels on ${formatDate(subscription.currentPeriodEnd)} — you'll keep Pro access until then.`
                : subscription.currentPeriodEnd
                  ? `Renews ${formatDate(subscription.currentPeriodEnd)}.`
                  : "Manage your subscription, payment method, and invoices below."}
            </p>
            <Button
              className="mt-6 w-full"
              size="lg"
              variant="accent"
              disabled={portalMutation.isPending}
              onClick={() => {
                setError(null);
                portalMutation.mutate();
              }}
            >
              {portalMutation.isPending ? "Opening billing portal…" : "Manage billing"}
            </Button>
          </>
        ) : (
          <>
            <p className="mt-2 text-sm text-ink-secondary">
              For a first, honest look at one site — 1 domain, 5 scans/month, Simple mode explanations.
            </p>
            <ul className="mt-6 space-y-2.5 border-t border-line pt-6 text-sm">
              {PRO_FEATURES.map((f) => (
                <li key={f} className="flex items-start gap-2.5 text-ink-secondary">
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-ink" />
                  {f}
                </li>
              ))}
            </ul>
            <Button
              className="mt-6 w-full"
              size="lg"
              variant="accent"
              disabled={checkoutMutation.isPending}
              onClick={() => {
                setError(null);
                checkoutMutation.mutate();
              }}
            >
              {checkoutMutation.isPending ? "Redirecting to checkout…" : "Upgrade to Pro"}
            </Button>
          </>
        )}
      </div>
    </div>
  );
}

export default function BillingPage() {
  return (
    <Suspense>
      <BillingContent />
    </Suspense>
  );
}
