import type { Grade } from "@/lib/types";
import { cn } from "@/lib/utils";

const GRADE_COLOR: Record<Grade, string> = {
  A: "#0ca30c",
  B: "#4f9d1f",
  C: "#c98500",
  D: "#ec835a",
  F: "#d03b3b",
};

export function GradeRing({
  grade,
  score,
  size = 88,
  showScore = true,
  trackColor = "#E3E0D2",
  scoreClassName = "text-ink-muted",
}: {
  grade: Grade;
  score: number;
  size?: number;
  showScore?: boolean;
  trackColor?: string;
  scoreClassName?: string;
}) {
  const stroke = Math.max(4, size * 0.09);
  const r = size / 2 - stroke;
  const c = 2 * Math.PI * r;
  const offset = c - (score / 100) * c;
  const color = GRADE_COLOR[grade];

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke={trackColor} strokeWidth={stroke} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={c}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div className="absolute flex flex-col items-center leading-none">
        <span className="font-serif" style={{ fontSize: size * 0.36, color }}>
          {grade}
        </span>
        {showScore && (
          <span className={cn("font-feature-tabular text-[11px]", scoreClassName)}>{score}/100</span>
        )}
      </div>
    </div>
  );
}
