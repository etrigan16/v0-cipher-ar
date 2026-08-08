import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import AttackSurfacePage from "@/app/dashboard/attack-surface/page"

const okJson = (data: unknown) => ({ ok: true, json: async () => data })

const asset = {
  id: "asset-1",
  domain: "example.com",
  subdomain: "www.example.com",
  ip: "93.184.216.34",
  port: 443,
  service: "https",
  fingerprint: { title: "Example Website" },
  status: "discovered",
  risk_score: 9.5,
  first_seen: "2025-01-01T00:00:00Z",
  last_seen: "2025-01-01T00:00:00Z",
}

describe("AttackSurfacePage", () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(okJson({ assets: [asset] })))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  it("loads and lists the tenant's assets", async () => {
    render(<AttackSurfacePage />)

    await waitFor(() => {
      expect(screen.getByText("www.example.com")).toBeInTheDocument()
    })
    expect(screen.getByText("93.184.216.34")).toBeInTheDocument()
    expect(screen.getByText("Example Website")).toBeInTheDocument()
  })

  it("shows the monitored asset count", async () => {
    render(<AttackSurfacePage />)

    await waitFor(() => {
      expect(screen.getByText("1")).toBeInTheDocument()
    })
  })

  it("starts a scan for the entered domain and refreshes assets", async () => {
    const fetchMock = vi.fn()
    fetchMock
      .mockResolvedValueOnce(okJson({ assets: [asset] })) // initial list
      .mockResolvedValueOnce(
        okJson({
          scan: {
            id: "scan-1",
            domain: "example.com",
            status: "complete",
            started_at: null,
            completed_at: null,
            created_at: "2025-01-01T00:00:00Z",
          },
          assets: [asset],
        })
      )
      .mockResolvedValueOnce(okJson({ assets: [asset] })) // refresh after scan
    vi.stubGlobal("fetch", fetchMock)

    render(<AttackSurfacePage />)

    await waitFor(() => {
      expect(screen.getByText("www.example.com")).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText(/dominio a escanear/i), {
      target: { value: "example.com" },
    })
    fireEvent.click(screen.getByRole("button", { name: /escanear/i }))

    const scanCall = fetchMock.mock.calls.find(
      ([url]) => typeof url === "string" && url.includes("/asm/scans")
    ) as [string, RequestInit] | undefined
    expect(scanCall).toBeDefined()

    await waitFor(() => {
      expect(screen.getByText(/Escaneo de example.com/)).toBeInTheDocument()
    })
  })

  it("shows an error when assets fail to load", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 401, json: async () => ({ detail: "Not authenticated" }) })
    )

    render(<AttackSurfacePage />)

    await waitFor(() => {
      expect(screen.getByText("Not authenticated")).toBeInTheDocument()
    })
  })

  it("shows the asset risk score column", async () => {
    render(<AttackSurfacePage />)

    await waitFor(() => {
      expect(screen.getByText("www.example.com")).toBeInTheDocument()
    })
    expect(screen.getByText("9.5")).toBeInTheDocument()
  })

  it("shows a dash for assets without a risk score", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(okJson({ assets: [{ ...asset, risk_score: null }] }))
    )

    render(<AttackSurfacePage />)

    await waitFor(() => {
      expect(screen.getByText("www.example.com")).toBeInTheDocument()
    })
    expect(screen.getByText("—")).toBeInTheDocument()
  })
})
