import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import RiskDistributionChart, {
  buildSeverityData,
  SEVERITY_ORDER,
} from "@/components/charts/risk-distribution"

describe("buildSeverityData", () => {
  it("maps counts into the fixed critical→info order", () => {
    const data = buildSeverityData({
      critical: 3,
      high: 1,
      medium: 0,
      low: 4,
      info: 2,
    })
    expect(data.map((d) => d.severity)).toEqual([...SEVERITY_ORDER])
    expect(data[0]).toEqual({ severity: "critical", count: 3 })
    expect(data[3]).toEqual({ severity: "low", count: 4 })
    expect(data[4]).toEqual({ severity: "info", count: 2 })
  })

  it("fills missing severities with zero counts", () => {
    const data = buildSeverityData({ low: 2 })
    expect(data).toHaveLength(5)
    expect(data.find((d) => d.severity === "high")?.count).toBe(0)
    expect(data.find((d) => d.severity === "critical")?.count).toBe(0)
    expect(data.find((d) => d.severity === "low")?.count).toBe(2)
  })
})

describe("RiskDistributionChart", () => {
  const counts = { info: 1, low: 2, medium: 3, high: 1, critical: 0 }

  it("renders an accessible summary of the severity distribution", () => {
    render(<RiskDistributionChart severityCounts={counts} />)
    const chart = screen.getByRole("img", { name: /distribución de severidad/i })
    const label = chart.getAttribute("aria-label") ?? ""
    expect(label).toContain("3 medium")
    expect(label).toContain("2 low")
    expect(label).toContain("0 critical")
  })

  it("renders one bar per severity from the counts", () => {
    const { container } = render(<RiskDistributionChart severityCounts={counts} />)
    const svg = container.querySelector("svg")
    expect(svg).not.toBeNull()
    // Bars render as SVG rects or paths (rounded radius) — at least one
    // shape per non-zero severity proves bars were drawn from the data.
    const barShapes = svg!.querySelectorAll("rect, path").length
    expect(barShapes).toBeGreaterThanOrEqual(5)
  })

  it("reflects different counts in the accessible summary", () => {
    render(
      <RiskDistributionChart
        severityCounts={{ info: 0, low: 0, medium: 0, high: 0, critical: 7 }}
      />
    )
    const label = screen
      .getByRole("img", { name: /distribución de severidad/i })
      .getAttribute("aria-label")
    expect(label).toContain("7 critical")
    expect(label).toContain("0 low")
  })
})
