"use client"

import { Bar, BarChart, Cell, Tooltip, XAxis, YAxis } from "recharts"

/** Fixed severity order — critical first so the most severe bar is leftmost. */
export const SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"] as const

export type SeverityDatum = { severity: string; count: number }

/** Map severity counts into the fixed chart order, zero-filling gaps. */
export function buildSeverityData(
  counts: Record<string, number>
): SeverityDatum[] {
  return SEVERITY_ORDER.map((severity) => ({
    severity,
    count: counts[severity] ?? 0,
  }))
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#dc2626",
  high: "#f97316",
  medium: "#eab308",
  low: "#22c55e",
  info: "#64748b",
}

export default function RiskDistributionChart({
  severityCounts,
}: {
  severityCounts: { info: number; low: number; medium: number; high: number; critical: number }
}) {
  const data = buildSeverityData(severityCounts)
  const summary = data.map((d) => `${d.count} ${d.severity}`).join(", ")

  return (
    <div
      role="img"
      aria-label={`Distribución de severidad: ${summary}`}
      className="w-full"
    >
      <BarChart
        width={560}
        height={200}
        data={data}
        margin={{ top: 8, right: 8, bottom: 0, left: -24 }}
      >
        <XAxis dataKey="severity" />
        {/* Numeric tick text is hidden: bars stay proportional, exact counts
            are in the Tooltip and the aria-label; keeps the SVG free of text
            nodes that would collide with page-level text queries. */}
        <YAxis allowDecimals={false} tick={false} />
        <Tooltip />
        <Bar dataKey="count" name="count" radius={[4, 4, 0, 0]} isAnimationActive={false}>
          {data.map((entry) => (
            <Cell
              key={entry.severity}
              fill={SEVERITY_COLORS[entry.severity] ?? "#64748b"}
            />
          ))}
        </Bar>
      </BarChart>
    </div>
  )
}
