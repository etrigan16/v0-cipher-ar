import { afterEach, describe, expect, it, vi } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import DashboardPage from "@/app/dashboard/page"

// The dashboard only reads the user's name; stub the auth context so the
// test focuses on the stats fetch without an extra /auth/me round-trip.
vi.mock("@/components/auth-context", () => ({
  useAuth: () => ({
    user: { id: "1", email: "user@example.com", name: "Test User", tenant: null },
  }),
}))

const okJson = (data: unknown) => ({ ok: true, json: async () => data })

describe("DashboardPage", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  it("shows real asset, finding, and scan counts from /asm/stats", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ assets: 3, findings: 2, scans: 1 }))
    vi.stubGlobal("fetch", fetchMock)

    render(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getByText("3")).toBeInTheDocument()
    })
    expect(screen.getByText("2")).toBeInTheDocument()
    expect(screen.getByText("1")).toBeInTheDocument()
    expect(screen.getByText("Vulnerabilidades activas")).toBeInTheDocument()
    expect(screen.getByText("Escaneos este mes")).toBeInTheDocument()

    const statsCall = fetchMock.mock.calls.find(
      ([url]) => typeof url === "string" && url.includes("/asm/stats")
    )
    expect(statsCall).toBeDefined()
  })

  it("falls back to zero counts when the stats request fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ detail: "Not authenticated" }),
      })
    )

    render(<DashboardPage />)

    await waitFor(() => {
      expect(screen.getAllByText("0").length).toBeGreaterThanOrEqual(3)
    })
    expect(screen.queryByText("…")).not.toBeInTheDocument()
  })

  it("shows a loading placeholder while counts are being fetched", async () => {
    // A never-resolving promise keeps the dashboard in its loading state.
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => {})))

    render(<DashboardPage />)

    expect(screen.getAllByText("…").length).toBeGreaterThan(0)
  })
})

describe("DashboardPage risk summary section", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  const riskSummary = {
    severity_counts: { info: 1, low: 2, medium: 3, high: 1, critical: 0 },
    avg_risk: 4.5,
    max_risk: 8.2,
    open_findings: 4,
    top_findings: [],
  }

  const routeFetch = (risk: unknown = riskSummary) =>
    vi.fn().mockImplementation((url: string) => {
      if (url.includes("/asm/risk-summary")) {
        return Promise.resolve(okJson(risk))
      }
      return Promise.resolve(okJson({ assets: 3, findings: 2, scans: 1 }))
    })

  it("renders the severity chart, average risk and open findings from /asm/risk-summary", async () => {
    const fetchMock = routeFetch()
    vi.stubGlobal("fetch", fetchMock)

    render(<DashboardPage />)

    await waitFor(() => {
      expect(
        screen.getByRole("img", { name: /distribución de severidad/i })
      ).toBeInTheDocument()
    })
    expect(screen.getByText(/riesgo promedio/i)).toBeInTheDocument()
    expect(screen.getByText("4.5")).toBeInTheDocument()
    expect(screen.getByText(/hallazgos abiertos/i)).toBeInTheDocument()
    expect(screen.getByText("4")).toBeInTheDocument()

    const summaryCall = fetchMock.mock.calls.find(
      ([url]) => typeof url === "string" && url.includes("/asm/risk-summary")
    )
    expect(summaryCall).toBeDefined()
  })

  it("links to the findings page", async () => {
    vi.stubGlobal("fetch", routeFetch())

    render(<DashboardPage />)

    await waitFor(() => {
      expect(
        screen.getByRole("link", { name: /ver hallazgos/i })
      ).toHaveAttribute("href", "/dashboard/findings")
    })
  })

  it("shows zeroed risk metrics when the summary request fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        if (url.includes("/asm/risk-summary")) {
          return Promise.resolve({
            ok: false,
            status: 401,
            json: async () => ({ detail: "Not authenticated" }),
          })
        }
        return Promise.resolve(okJson({ assets: 3, findings: 2, scans: 1 }))
      })
    )

    render(<DashboardPage />)

    await waitFor(() => {
      expect(
        screen.getByRole("img", { name: /distribución de severidad/i })
      ).toBeInTheDocument()
    })
    expect(screen.getByText(/riesgo promedio/i)).toBeInTheDocument()
    // avg risk and open findings fall back to zero when the summary fails.
    expect(screen.getAllByText("0").length).toBeGreaterThanOrEqual(2)
  })
})
