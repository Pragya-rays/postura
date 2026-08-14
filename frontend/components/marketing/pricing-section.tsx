import Link from "next/link";
import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";

const free = [
  "1 domain",
  "3 scans per month",
  "Letter grade + Start here fixes",
  "Simple mode explanations",
];

const pro = [
  "10 domains",
  "Unlimited scans",
  "Simple and Technical mode",
  "PDF export for clients",
  "Weekly re-scan with change alerts",
];

export function PricingSection() {
  return (
    <section id="pricing" className="bg-forest-soft py-24">
      <div className="container">
        <div className="mx-auto max-w-xl text-center">
          <p className="text-[12px] font-semibold uppercase tracking-wide text-forest-muted">Pricing</p>
          <h2 className="mt-3 text-balance font-serif text-[34px] leading-tight text-forest-ink sm:text-[40px]">
            Start free. Upgrade when you outgrow it.
          </h2>
        </div>

        <div className="mx-auto mt-14 grid max-w-3xl gap-6 sm:grid-cols-2">
          <div className="flex flex-col rounded-xl2 border border-forest-line bg-forest-card p-8">
            <p className="text-[13px] font-semibold uppercase tracking-wide text-forest-muted">Free</p>
            <p className="mt-3 font-serif text-4xl text-forest-ink">
              $0<span className="text-base font-sans font-normal text-forest-muted"> forever</span>
            </p>
            <Link href="/register" className="mt-6">
              <Button variant="outline-on-dark" size="lg" className="w-full text-forest-ink">
                Get started free
              </Button>
            </Link>
            <ul className="mt-8 space-y-3.5 border-t border-forest-line pt-6 text-sm">
              {free.map((item) => (
                <li key={item} className="flex items-start gap-2.5 text-forest-secondary">
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-lime" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="glow-ring flex flex-col rounded-xl2 border border-forest-line bg-forest-card p-8">
            <p className="text-[13px] font-semibold uppercase tracking-wide text-lime">Pro</p>
            <p className="mt-3 font-serif text-4xl text-forest-ink">
              $19<span className="text-base font-sans font-normal text-forest-muted"> per month</span>
            </p>
            <Link href="/register" className="mt-6">
              <Button variant="on-dark" size="lg" className="w-full">
                Get started
              </Button>
            </Link>
            <ul className="mt-8 space-y-3.5 border-t border-forest-line pt-6 text-sm">
              {pro.map((item) => (
                <li key={item} className="flex items-start gap-2.5 text-forest-secondary">
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-lime" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
