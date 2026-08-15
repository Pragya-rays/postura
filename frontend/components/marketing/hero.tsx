import Link from "next/link";
import { ArrowRight, ShieldCheck, CircleCheckBig } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AuroraField } from "@/components/marketing/aurora-field";

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-cream py-10 text-ink sm:py-14 lg:py-20">
      <AuroraField />
      <div className="pointer-events-none absolute inset-0 bg-grid opacity-30" />

      <div className="container relative grid gap-8 md:gap-10 lg:grid-cols-[1.02fr_0.98fr] lg:items-center">
        <div className="max-w-2xl">
          <p className="text-[12px] font-semibold uppercase tracking-[0.38em] text-ink-muted">
            Website security, in plain English
          </p>

          <h1 className="mt-4 text-balance font-serif text-[34px] leading-[1.03] tracking-[-0.04em] sm:mt-5 sm:text-[46px] md:text-[56px] lg:text-[68px]">
            Find out what your website is quietly getting wrong.
          </h1>

          <p className="mt-4 max-w-xl text-[15px] leading-7 text-ink-secondary sm:text-[16px] sm:leading-8">
            Postura checks your SSL, security headers, cookies and DNS, then uses AI to explain
            each finding in plain English and hands you the exact lines to copy and paste. No
            jargon, no consultant required.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-2.5 sm:mt-8 sm:gap-3">
            <Link href="/register">
              <Button variant="accent" size="lg">
                Scan my site
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <span className="rounded-full border border-line bg-cream-card px-3 py-1.5 text-xs text-ink-secondary sm:px-4 sm:py-2 sm:text-sm">
              Free scan in about 60 seconds
            </span>
          </div>

          <p className="mt-4 text-xs text-ink-muted sm:mt-6 sm:text-sm">
            Free · No signup for a basic scan · Takes about 60 seconds
          </p>
        </div>

        <div className="relative w-full max-w-xl lg:justify-self-end">
          <div className="absolute -inset-4 rounded-[2rem] bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.08),transparent_62%)] blur-3xl" />
          <div className="relative overflow-hidden rounded-[2rem] border border-line bg-cream-card p-6 shadow-pop sm:p-7">
            <div className="flex items-center gap-3 border-b border-line pb-4 sm:gap-4 sm:pb-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-lime-soft sm:h-12 sm:w-12">
                <ShieldCheck className="h-5 w-5 text-ink sm:h-6 sm:w-6" />
              </div>
              <div>
                <p className="text-[12px] font-semibold uppercase tracking-[0.28em] text-ink-muted">
                  Scan preview
                </p>
                <p className="mt-1 font-serif text-xl text-ink sm:text-2xl">Site health snapshot</p>
              </div>
            </div>

            <div className="mt-4 space-y-2.5 sm:mt-5 sm:space-y-3">
              {[
                ["SSL / TLS", "Healthy"],
                ["Security headers", "2 missing"],
                ["Cookies", "1 issue"],
                ["DNS / auth", "Needs review"],
              ].map(([label, value], index) => (
                <div key={label} className="flex items-center justify-between rounded-xl2 border border-line bg-cream px-3 py-2.5 sm:px-4 sm:py-3">
                  <div className="flex items-center gap-2.5">
                    <CircleCheckBig className={["h-4 w-4", index === 0 ? "text-lime" : "text-ink-muted"].join(" ")} />
                    <span className="text-xs text-ink-secondary sm:text-sm">{label}</span>
                  </div>
                  <span className="text-xs font-medium text-ink sm:text-sm">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
