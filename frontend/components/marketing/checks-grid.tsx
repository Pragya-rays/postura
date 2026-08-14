import { Lock, ShieldAlert, Cookie, Mail, FileSearch, Fingerprint } from "lucide-react";

const checks = [
  {
    icon: Lock,
    title: "SSL certificate",
    body: "Validity, expiry runway, issuer and whether old TLS versions are still accepted.",
  },
  {
    icon: ShieldAlert,
    title: "Security headers",
    body: "HSTS, CSP, frame options and the rest, with the exact header line to add.",
  },
  {
    icon: Cookie,
    title: "Cookies",
    body: "Secure, HttpOnly and SameSite attributes on everything your site sets.",
  },
  {
    icon: Mail,
    title: "DNS & email",
    body: "SPF, DMARC, CAA and nameserver setup that stops people spoofing your domain.",
  },
  {
    icon: FileSearch,
    title: "robots.txt & sitemap",
    body: "Whether crawlers can read you properly, and if you're leaking staging paths.",
  },
  {
    icon: Fingerprint,
    title: "Technology detection",
    body: "The CMS, frameworks and analytics we can see, and known-outdated versions.",
  },
];

export function ChecksGrid() {
  return (
    <section id="checks" className="bg-forest py-24">
      <div className="container">
        <div className="max-w-2xl">
          <p className="text-[12px] font-semibold uppercase tracking-wide text-forest-muted">What we check</p>
          <h2 className="mt-3 text-balance font-serif text-[34px] leading-tight text-forest-ink sm:text-[40px]">
            Six checks, one readable report.
          </h2>
        </div>

        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {checks.map((c) => {
            const Icon = c.icon;
            return (
              <div
                key={c.title}
                className="group rounded-xl2 border border-forest-line bg-forest-card p-6 transition-colors hover:border-lime/30"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-lime/10">
                  <Icon className="h-5 w-5 text-lime" />
                </div>
                <h3 className="mt-4 font-serif text-[17px] text-forest-ink">{c.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-forest-secondary">{c.body}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
