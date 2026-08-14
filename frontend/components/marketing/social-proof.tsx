const teams = [
  "Northwind Studio",
  "Halcyon Dental",
  "Meridian Books",
  "Fairhaven Legal",
  "Copperline Coffee",
  "Atlas Rentals",
  "Brightpath Clinic",
  "Ledgerwise",
];

export function SocialProof() {
  return (
    <section className="border-y border-line bg-cream py-10">
      <div className="container">
        <p className="text-center text-[12px] font-semibold uppercase tracking-[0.3em] text-ink-muted">
          Scanning sites for teams like these
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-x-10 gap-y-3">
          {teams.map((name) => (
            <span key={name} className="text-[15px] font-medium text-ink-muted/80">
              {name}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
