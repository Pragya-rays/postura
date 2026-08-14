import { AlertTriangle, CircleAlert, CheckCircle2 } from "lucide-react";

const fixFirst = [{ title: "Missing HSTS header", meta: "10 min fix" }];

const worthFixing = [
  { title: "Missing Content-Security-Policy", meta: "30 min fix" },
  { title: "HttpOnly cookie attribute missing", meta: "5 min fix" },
];

const passed = [
  "Valid SSL certificate (Let's Encrypt, 68 days remaining)",
  "Modern TLS only (1.2 & 1.3)",
  "No MIME sniffing enabled",
  "robots.txt & sitemap accessible",
];

export function SampleReport() {
  return (
    <section id="sample-report" className="bg-forest-soft py-24">
      <div className="container grid gap-12 lg:grid-cols-[0.85fr_1.15fr] lg:items-center">
        <div>
          <p className="text-[12px] font-semibold uppercase tracking-wide text-forest-muted">Sample report</p>
          <h2 className="mt-3 text-balance font-serif text-[34px] leading-tight text-forest-ink sm:text-[40px]">
            One grade. Every reason behind it.
          </h2>
          <p className="mt-4 text-[16px] leading-relaxed text-forest-secondary">
            Findings are sorted by what to fix first, not by how alarming they sound.
            Everything else you're already doing right shows up too.
          </p>
        </div>

        <div className="rounded-xl2 border border-forest-line bg-forest-card p-7 shadow-pop-dark">
          <div className="flex items-center gap-5">
            <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full border-2 border-status-warning font-serif text-3xl text-forest-ink">
              C
            </div>
            <div>
              <p className="font-serif text-2xl text-forest-ink">68 / 100</p>
              <p className="text-sm text-forest-muted">Example scan result</p>
            </div>
          </div>

          <div className="mt-6 space-y-2">
            <p className="text-[12px] font-semibold uppercase tracking-wide text-status-critical">Fix first</p>
            {fixFirst.map((f) => (
              <div
                key={f.title}
                className="flex items-center justify-between gap-3 rounded-xl2 border border-forest-line bg-forest px-4 py-3"
              >
                <span className="flex items-center gap-2.5 text-sm text-forest-ink">
                  <CircleAlert className="h-4 w-4 shrink-0 text-status-critical" />
                  {f.title}
                </span>
                <span className="shrink-0 text-xs text-forest-muted">{f.meta}</span>
              </div>
            ))}
          </div>

          <div className="mt-5 space-y-2">
            <p className="text-[12px] font-semibold uppercase tracking-wide text-status-warning">Worth fixing</p>
            {worthFixing.map((f) => (
              <div
                key={f.title}
                className="flex items-center justify-between gap-3 rounded-xl2 border border-forest-line bg-forest px-4 py-3"
              >
                <span className="flex items-center gap-2.5 text-sm text-forest-ink">
                  <AlertTriangle className="h-4 w-4 shrink-0 text-status-warning" />
                  {f.title}
                </span>
                <span className="shrink-0 text-xs text-forest-muted">{f.meta}</span>
              </div>
            ))}
          </div>

          <div className="mt-5 space-y-2">
            <p className="text-[12px] font-semibold uppercase tracking-wide text-status-good">Passed</p>
            {passed.map((title) => (
              <div
                key={title}
                className="flex items-center gap-2.5 rounded-xl2 border border-forest-line bg-forest px-4 py-3"
              >
                <CheckCircle2 className="h-4 w-4 shrink-0 text-status-good" />
                <span className="text-sm text-forest-secondary">{title}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
