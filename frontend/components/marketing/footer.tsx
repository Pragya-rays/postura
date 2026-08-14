import Link from "next/link";
import { Logo } from "./logo";

const columns = [
  {
    title: "Product",
    links: [
      { label: "Pricing", href: "/pricing" },
      { label: "Dashboard", href: "/dashboard" },
      { label: "Sample report", href: "/#sample-report" },
    ],
  },
  {
    title: "Resources",
    links: [
      { label: "Docs", href: "#" },
      { label: "Check reference", href: "/#checks" },
      { label: "Changelog", href: "#" },
    ],
  },
  {
    title: "More",
    links: [
      { label: "GitHub", href: "#" },
      { label: "Security disclaimer", href: "#" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="border-t border-forest-line bg-forest py-14">
      <div className="container grid gap-10 sm:grid-cols-2 lg:grid-cols-[1.2fr_1fr_1fr_1fr]">
        <div>
          <Logo dark />
          <p className="mt-3 max-w-xs text-sm leading-relaxed text-forest-secondary">
            Website security, in plain English. Free basic scan, no signup.
          </p>
        </div>
        {columns.map((col) => (
          <div key={col.title}>
            <p className="text-[12px] font-semibold uppercase tracking-wide text-forest-muted">{col.title}</p>
            <ul className="mt-4 space-y-2.5">
              {col.links.map((l) => (
                <li key={l.label}>
                  <Link href={l.href} className="text-sm text-forest-secondary hover:text-forest-ink">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="container mt-12 flex flex-wrap items-center justify-between gap-2 border-t border-forest-line pt-6 text-xs text-forest-muted">
        <span>© 2026 Postura.</span>
        <span>
          Made with <span className="text-red-500">❤️</span> by Pragya
        </span>
      </div>
    </footer>
  );
}
