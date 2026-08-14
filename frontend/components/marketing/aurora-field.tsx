import { cn } from "@/lib/utils";

/**
 * Drifting, blurred color-field background. Three soft grey blobs at
 * different lightness levels slowly pan and scale behind the content —
 * enough tonal variation to still read as three overlapping shapes, no
 * hue. Pure CSS transforms, no canvas/WebGL, and respects
 * prefers-reduced-motion.
 */
export function AuroraField({ className, subtle = false }: { className?: string; subtle?: boolean }) {
  const base = subtle ? 0.16 : 0.32;
  return (
    <div className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)} aria-hidden>
      <div
        className="absolute left-[-14%] top-[-24%] h-[clamp(220px,42vw,520px)] w-[clamp(220px,42vw,520px)] animate-aurora-1 rounded-full blur-3xl"
        style={{ background: `radial-gradient(circle, rgba(196,196,196,${base}) 0%, rgba(196,196,196,0) 70%)` }}
      />
      <div
        className="absolute right-[-18%] top-[-14%] h-[clamp(210px,38vw,480px)] w-[clamp(210px,38vw,480px)] animate-aurora-2 rounded-full blur-3xl"
        style={{ background: `radial-gradient(circle, rgba(140,140,140,${base}) 0%, rgba(140,140,140,0) 70%)` }}
      />
      <div
        className="absolute bottom-[-34%] left-[10%] h-[clamp(240px,45vw,560px)] w-[clamp(240px,45vw,560px)] animate-aurora-3 rounded-full blur-3xl sm:left-[18%]"
        style={{ background: `radial-gradient(circle, rgba(168,168,168,${base}) 0%, rgba(168,168,168,0) 70%)` }}
      />
    </div>
  );
}
