"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { SEVERITY_LABEL, SEVERITY_ORDER, type Severity } from "@/lib/types";

// Status palette (fixed, never themed) — see dataviz skill references/palette.md.
const STATUS_COLOR: Record<Severity, string> = {
  critical: "#d03b3b",
  high: "#ec835a",
  medium: "#fab219",
  low: "#0ca30c",
  info: "#8A8C7E",
};

export function SeverityChart({ breakdown }: { breakdown: Record<Severity, number> }) {
  const data = SEVERITY_ORDER.map((sev) => ({
    severity: sev,
    label: SEVERITY_LABEL[sev],
    count: breakdown[sev] ?? 0,
  })).filter((d) => d.count > 0);

  if (data.length === 0) {
    return <p className="text-sm text-ink-muted">No findings to chart — clean scan.</p>;
  }

  return (
    <div className="h-[168px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 28, bottom: 4, left: 0 }} barCategoryGap={10}>
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="label"
            width={92}
            tickLine={false}
            axisLine={false}
            tick={{ fill: "#55584C", fontSize: 13 }}
          />
          <Tooltip
            cursor={{ fill: "rgba(18,20,15,0.04)" }}
            contentStyle={{
              borderRadius: 10,
              border: "1px solid #E3E0D2",
              fontSize: 13,
              background: "#FFFFFF",
            }}
            formatter={(value: number) => [`${value} finding${value === 1 ? "" : "s"}`, ""]}
            labelFormatter={() => ""}
          />
          <Bar dataKey="count" radius={4} maxBarSize={18} label={{ position: "right", fill: "#12140F", fontSize: 12 }}>
            {data.map((d) => (
              <Cell key={d.severity} fill={STATUS_COLOR[d.severity]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
