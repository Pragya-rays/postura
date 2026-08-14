"use client";

import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatDate } from "@/lib/utils";

export function GradeTrendChart({ points }: { points: { date: string; score: number }[] }) {
  if (points.length < 2) {
    return <p className="text-[13px] text-ink-muted">Scan again to start a trend line.</p>;
  }

  return (
    <div className="h-[88px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={points} margin={{ top: 6, right: 4, bottom: 0, left: 4 }}>
          <defs>
            <linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#12140F" stopOpacity={0.14} />
              <stop offset="100%" stopColor="#12140F" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="date" hide />
          <YAxis domain={[0, 100]} hide />
          <Tooltip
            cursor={{ stroke: "#E3E0D2" }}
            contentStyle={{
              borderRadius: 10,
              border: "1px solid #E3E0D2",
              fontSize: 12,
              background: "#FFFFFF",
            }}
            labelFormatter={(d: string) => formatDate(d)}
            formatter={(value: number) => [`${value}/100`, "Score"]}
          />
          <Area
            type="monotone"
            dataKey="score"
            stroke="#12140F"
            strokeWidth={2}
            fill="url(#scoreFill)"
            dot={{ r: 3, fill: "#12140F", strokeWidth: 0 }}
            activeDot={{ r: 5 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
