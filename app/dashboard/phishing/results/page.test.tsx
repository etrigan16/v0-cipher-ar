import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import ResultsPage from "@/app/dashboard/phishing/results/page"

const okJson = (data: unknown) => ({ ok: true, json: async () => data })

const campaign = {
  id: "camp-1",
  name: "Campaña Q1",
  template_id: "tpl-1",
  status: "active",
  started_at: null,
  completed_at: null,
  created_at: "2025-01-01T00:00:00Z",
  target_count: 2,
}

describe("ResultsPage (overview)", () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  it("loads the tenant summary and renders the aggregate cards", async () => {
    const summary = {
      total_targets: 10,
      sent: 10,
      opened_count: 4,
      opened_rate: 40.0,
      clicked_count: 2,
      clicked_rate: 20.0,
      credentials_count: 1,
      reported_count: 0,
    }
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/results-summary")) {
        return Promise.resolve(okJson(summary))
      }
      return Promise.resolve(okJson({ campaigns: [campaign] }))
    })
    vi.stubGlobal("fetch", fetchMock)

    render(<ResultsPage />)

    await waitFor(() => {
      expect(screen.getByText("4 (40%)")).toBeInTheDocument()
    })
    expect(screen.getByText("2 (20%)")).toBeInTheDocument()
    expect(screen.getByText("1")).toBeInTheDocument() // credentials
  })

  it("lists campaigns and links each one to its per-campaign results", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/results-summary")) {
        return Promise.resolve(
          okJson({
            total_targets: 0,
            sent: 0,
            opened_count: 0,
            opened_rate: 0,
            clicked_count: 0,
            clicked_rate: 0,
            credentials_count: 0,
            reported_count: 0,
          })
        )
      }
      return Promise.resolve(okJson({ campaigns: [campaign] }))
    })
    vi.stubGlobal("fetch", fetchMock)

    render(<ResultsPage />)

    await waitFor(() => {
      expect(screen.getByText("Campaña Q1")).toBeInTheDocument()
    })

    const link = screen.getByRole("link", { name: /campaña q1/i })
    expect(link).toHaveAttribute("href", "/dashboard/phishing/results/camp-1")
  })

  it("shows an empty state when the tenant has no activity", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/results-summary")) {
        return Promise.resolve(
          okJson({
            total_targets: 0,
            sent: 0,
            opened_count: 0,
            opened_rate: 0,
            clicked_count: 0,
            clicked_rate: 0,
            credentials_count: 0,
            reported_count: 0,
          })
        )
      }
      return Promise.resolve(okJson({ campaigns: [] }))
    })
    vi.stubGlobal("fetch", fetchMock)

    render(<ResultsPage />)

    await waitFor(() => {
      expect(screen.getByText(/Sin actividad/i)).toBeInTheDocument()
    })
  })
})
