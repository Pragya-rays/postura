import { Globe, ScanSearch, FileCheck2 } from "lucide-react";

const steps = [
  {
    icon: Globe,
    number: "01",
    title: "Enter your domain",
    body: "Type the address you'd give a customer. No code to install, nothing to verify, no access needed.",
  },
  {
    icon: ScanSearch,
    number: "02",
    title: "We check it",
    body: "Postura looks at your certificate, headers, cookies, DNS records and public files the way a browser does.",
  },
  {
    icon: FileCheck2,
    number: "03",
    title: "Get plain-English fixes",
    body: "Each finding comes with what it means, why it matters, and the exact configuration line to paste.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-forest py-24">
      <div className="container">
        <div className="max-w-2xl">
          <p className="text-[12px] font-semibold uppercase tracking-wide text-lime">How it works</p>
          <h2 className="mt-3 text-balance font-serif text-[34px] leading-tight text-forest-ink sm:text-[40px]">
            Three steps, about a minute.
          </h2>
        </div>

        <div className="mt-14 grid gap-5 lg:grid-cols-3">
          {steps.map((s) => {
            const Icon = s.icon;
            return (
              <div key={s.number} className="rounded-xl2 border border-forest-line bg-forest-card p-6">
                <div className="flex items-center justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-lime/15">
                    <Icon className="h-5 w-5 text-lime" />
                  </div>
                  <span className="font-mono text-[13px] text-forest-muted">{s.number}</span>
                </div>
                <h3 className="mt-4 font-serif text-xl text-forest-ink">{s.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-forest-secondary">{s.body}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
