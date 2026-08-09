import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import ResultsDetailPage from "@/app/dashboard/phishing/results/[id]/page"

const okJson = (data: unknown) => ({ ok: true, json: async () => data })

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "camp-1" }),
}))

const targetResult = {
  email: "a@b.com",
  name: "Ana",
  status: "active",
  opened: true,
  opened_at: "2025-01-02T10:00:00Z",
  clicked: true,
  clicked_at: "2025-01-02T10:05:00Z",
  credential: false,
  credential_at: null,
  reported: false,
  reported_at: null,
}

describe("ResultsDetailPage ([id])", () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it("renders the per-target results table with activity flags", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      okJson({
        campaign_id: "camp-1",
        targets: [targetResult],
      })
    )
    vi.stubGlobal("fetch", fetchMock)

    render(<ResultsDetailPage />)

    await waitFor(() => {
      expect(screen.getByText("a@b.com")).toBeInTheDocument()
    })
    expect(screen.getByText("Ana")).toBeInTheDocument()
    expect(screen.getAllByText("true").length).toBe(2) // opened + clicked
  })

  it("shows an empty state when the campaign has no targets", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(okJson({ campaign_id: "camp-1", targets: [] }))
    )

    render(<ResultsDetailPage />)

    await waitFor(() => {
      expect(screen.getByText(/Sin resultados/i)).toBeInTheDocument()
    })
  })

  it("exports CSV via blob download", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/export?format=csv")) {
        return Promise.resolve({
          ok: true,
          blob: async () => new Blob(["email,name\n"], { type: "text/csv" }),
        })
      }
      return Promise.resolve(
        okJson({
          campaign_id: "camp-1",
          targets: [targetResult],
        })
      )
    })
    vi.stubGlobal("fetch", fetchMock)
    const createObjectURL = vi.fn(() => "blob:mock")
    vi.stubGlobal("URL", { ...URL, createObjectURL })

    render(<ResultsDetailPage />)

    await waitFor(() => {
      expect(screen.getByText("a@b.com")).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole("button", { name: /exportar csv/i }))

    await waitFor(() => {
      const exportCall = fetchMock.mock.calls.find(
        ([url]) => typeof url === "string" && url.includes("/export?format=csv")
      )
      expect(exportCall).toBeDefined()
      expect(createObjectURL).toHaveBeenCalled()
    })
  })

  it("exports PDF via blob download", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/export?format=pdf")) {
        return Promise.resolve({
          ok: true,
          blob: async () => new Blob(["%PDF"], { type: "application/pdf" }),
        })
      }
      return Promise.resolve(
        okJson({
          campaign_id: "camp-1",
          targets: [targetResult],
        })
      )
    })
    vi.stubGlobal("fetch", fetchMock)
    const createObjectURL = vi.fn(() => "blob:mock")
    vi.stubGlobal("URL", { ...URL, createObjectURL })

    render(<ResultsDetailPage />)

    await waitFor(() => {
      expect(screen.getByText("a@b.com")).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole("button", { name: /exportar pdf/i }))

    await waitFor(() => {
      const exportCall = fetchMock.mock.calls.find(
        ([url]) => typeof url === "string" && url.includes("/export?format=pdf")
      )
      expect(exportCall).toBeDefined()
      expect(createObjectURL).toHaveBeenCalled()
    })
  })
})
