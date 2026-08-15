import Link from "next/link";
import { Check, Minus } from "lucide-react";
import { Navbar } from "@/components/marketing/navbar";
import { Footer } from "@/components/marketing/footer";
import { AuroraField } from "@/components/marketing/aurora-field";
import { Button } from "@/components/ui/button";

type Row = {
  label: string;
  free: string | boolean;
  pro: string | boolean;
};

const rows: Row[] = [
  { label: "Domains", free: "1", pro: "10" },
  { label: "Scans / month", free: "5", pro: "Unlimited (fair-use capped)" },
  { label: "Report mode", free: "Simple only", pro: "Simple + Technical (CVSS, OWASP, raw evidence)" },
  { label: "History retention", free: "30 days", pro: "Unlimited" },
  { label: "PDF export", free: false, pro: true },
  { label: "Active scanning (v2)", free: false, pro: "Included, credit-based" },
];

function Cell({ value }: { value: string | boolean }) {
  if (value === true) {
    return (
      <span className="inline-flex items-center gap-1.5 text-forest-ink">
        <Check className="h-4 w-4 text-lime" /> Included
      </span>
    );
  }
  if (value === false) {
    return (
      <span className="inline-flex items-center gap-1.5 text-forest-muted">
        <Minus className="h-4 w-4" /> —
      </span>
    );
  }
  return <span className="text-forest-ink">{value}</span>;
}

export default function PricingPage() {
  return (
    <main className="bg-forest">
      <Navbar />

      <section className="relative overflow-hidden">
        <AuroraField subtle />
        <div className="pointer-events-none absolute inset-0 bg-grid-dark opacity-60" />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-forest/0 via-forest/10 to-forest" />

        <div className="container relative py-20 lg:py-28">
          <div className="mx-auto max-w-2xl text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-forest-line bg-forest-card/70 px-3 py-1 text-[12px] font-semibold uppercase tracking-wide text-forest-muted">
              <Check className="h-3.5 w-3.5 text-lime" />
              Ownership verification is free forever
            </div>
            <h1 className="mt-6 text-balance font-serif text-[38px] leading-[1.1] text-forest-ink sm:text-[48px]">
              Simple pricing, gated by depth — never by safety.
            </h1>
            <p className="mt-5 text-[16px] leading-relaxed text-forest-secondary">
              Free covers everything you need to check one site properly. Pro adds
              room to grow — more domains, unlimited scans, full technical detail,
              and exportable reports.
            </p>
          </div>

          <div className="mx-auto mt-14 grid max-w-3xl gap-6 sm:grid-cols-2">
            {/* Free */}
            <div className="flex flex-col rounded-xl2 border border-forest-line bg-forest-card p-8">
              <p className="text-[13px] font-semibold uppercase tracking-wide text-forest-muted">Free</p>
              <p className="mt-3 font-serif text-4xl text-forest-ink">
                $0<span className="text-base font-sans font-normal text-forest-muted">/mo</span>
              </p>
              <p className="mt-2 text-sm text-forest-secondary">
                For a first, honest look at one site.
              </p>
              <Link href="/register" className="mt-6">
                <Button variant="outline-on-dark" size="lg" className="w-full text-forest-ink">
                  Get started free
                </Button>
              </Link>
              <ul className="mt-8 space-y-3.5 border-t border-forest-line pt-6 text-sm">
                {rows.map((r) => (
                  <li key={r.label} className="flex items-center justify-between gap-4">
                    <span className="text-forest-secondary">{r.label}</span>
                    <Cell value={r.free} />
                  </li>
                ))}
              </ul>
            </div>

            {/* Pro */}
            <div className="glow-ring flex flex-col rounded-xl2 border border-forest-line bg-forest-card p-8">
              <div className="flex items-center justify-between">
                <p className="text-[13px] font-semibold uppercase tracking-wide text-lime">Pro</p>
                <span className="rounded-full bg-lime/15 px-2.5 py-0.5 text-[11px] font-semibold text-lime">
                  Most popular
                </span>
              </div>
              <p className="mt-3 font-serif text-4xl text-forest-ink">
                $19<span className="text-base font-sans font-normal text-forest-muted">/mo</span>
              </p>
              <p className="mt-2 text-sm text-forest-secondary">
                Illustrative price — for agencies and multi-site owners.
              </p>
              <Link href="/dashboard/billing" className="mt-6">
                <Button variant="on-dark" size="lg" className="w-full">
                  Upgrade to Pro
                </Button>
              </Link>
              <ul className="mt-8 space-y-3.5 border-t border-forest-line pt-6 text-sm">
                {rows.map((r) => (
                  <li key={r.label} className="flex items-center justify-between gap-4">
                    <span className="text-forest-secondary">{r.label}</span>
                    <Cell value={r.pro} />
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <p className="mx-auto mt-8 max-w-xl text-center text-[13px] text-forest-muted">
            Prices shown are illustrative. Billing runs on Stripe Checkout + the
            Stripe Billing Portal — plan changes are always applied server-side
            from a verified webhook, never from the browser.
          </p>
        </div>
      </section>

      <Footer />
    </main>
  );
}
