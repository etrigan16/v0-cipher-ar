import { afterEach, describe, expect, it, vi } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import FindingsPage from "@/app/dashboard/findings/page"

const okJson = (data: unknown) => ({ ok: true, json: async () => data })
const okBlob = (content: string) => ({
  ok: true,
  blob: async () => new Blob([content]),
})

const finding = {
  id: "f-1",
  asset_id: "asset-1",
  severity: "high",
  title: "TLS certificate expired",
  detail: "cert expired",
  risk_score: 9.5,
  risk_level: "critical",
  finding_type: "tls-expired",
  remediation: "Renew the certificate",
  status: "open",
  enriched_at: null,
  discovered_at: "2025-01-01T00:00:00Z",
}

const assets = [
  {
    id: "asset-1",
    domain: "example.com",
    subdomain: "www.example.com",
    ip: "93.184.216.34",
    port: 443,
    service: "https",
    fingerprint: { title: "Example" },
    status: "discovered",
    risk_score: 9.5,
    first_seen: "2025-01-01T00:00:00Z",
    last_seen: "2025-01-01T00:00:00Z",
  },
]

type RouteOptions = {
  findings?: unknown[]
  assets?: unknown[]
  patchResult?: unknown
  enrichResult?: unknown
}

function routeFetch({ findings = [], assets = [], patchResult, enrichResult }: RouteOptions = {}) {
  return vi.fn().mockImplementation((url: string, options?: RequestInit) => {
    const u = String(url)
    const method = options?.method ?? "GET"
    if (method === "POST" && u.includes("/enrich")) {
      return Promise.resolve(okJson(enrichResult ?? finding))
    }
    if (method === "PATCH" && u.includes("/asm/findings/")) {
      return Promise.resolve(okJson(patchResult ?? finding))
    }
    if (u.includes("/asm/findings")) {
      return Promise.resolve(
        okJson({ findings, total: findings.length, limit: 100, offset: 0 })
      )
    }
    if (u.includes("/asm/assets")) {
      return Promise.resolve(okJson({ assets }))
    }
    if (u.includes("/asm/export")) {
      return Promise.resolve(okBlob("a,b\n"))
    }
    return Promise.resolve(okJson({}))
  })
}

describe("FindingsPage", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
    localStorage.clear()
  })

  it("loads and lists the tenant's findings with asset names", async () => {
    const fetchMock = routeFetch({ findings: [finding], assets })
    vi.stubGlobal("fetch", fetchMock)

    render(<FindingsPage />)

    await waitFor(() => {
      expect(screen.getByText("TLS certificate expired")).toBeInTheDocument()
    })
    expect(screen.getByText("www.example.com")).toBeInTheDocument()
    expect(screen.getByText("9.5")).toBeInTheDocument()
    expect(screen.getByText("high")).toBeInTheDocument()
    expect(screen.getByText("open")).toBeInTheDocument()

    const findingsCall = fetchMock.mock.calls.find(([u]) =>
      String(u).includes("/asm/findings")
    )
    expect(findingsCall).toBeDefined()
  })

  it("refetches with the severity filter when it changes", async () => {
    const fetchMock = routeFetch({ findings: [finding], assets })
    vi.stubGlobal("fetch", fetchMock)

    render(<FindingsPage />)

    await waitFor(() => {
      expect(screen.getByText("TLS certificate expired")).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText(/filtrar por severidad/i), {
      target: { value: "high" },
    })

    await waitFor(() => {
      const call = fetchMock.mock.calls.find(([u]) =>
        String(u).includes("/asm/findings") && String(u).includes("severity=high")
      )
      expect(call).toBeDefined()
    })
  })

  it("refetches with the status filter when it changes", async () => {
    const fetchMock = routeFetch({ findings: [finding], assets })
    vi.stubGlobal("fetch", fetchMock)

    render(<FindingsPage />)

    await waitFor(() => {
      expect(screen.getByText("TLS certificate expired")).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText(/filtrar por estado/i), {
      target: { value: "open" },
    })

    await waitFor(() => {
      const call = fetchMock.mock.calls.find(([u]) =>
        String(u).includes("/asm/findings") && String(u).includes("status=open")
      )
      expect(call).toBeDefined()
    })
  })

  it("resolves a finding via PATCH and updates the row", async () => {
    const fetchMock = routeFetch({
      findings: [finding],
      assets,
      patchResult: { ...finding, status: "resolved" },
    })
    vi.stubGlobal("fetch", fetchMock)

    render(<FindingsPage />)

    await waitFor(() => {
      expect(screen.getByText("TLS certificate expired")).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole("button", { name: /resolver hallazgo/i }))

    await waitFor(() => {
      expect(screen.getByText("resolved")).toBeInTheDocument()
    })
    expect(screen.queryByText("open")).not.toBeInTheDocument()

    const patchCall = fetchMock.mock.calls.find(
      ([u, o]) => String(u).includes("/asm/findings/") && o?.method === "PATCH"
    ) as [string, RequestInit] | undefined
    expect(patchCall).toBeDefined()
    expect(JSON.parse((patchCall![1].body as string) ?? "{}")).toEqual({
      status: "resolved",
    })
  })

  it("enriches a finding via POST and shows the enriched date", async () => {
    const fetchMock = routeFetch({
      findings: [finding],
      assets,
      enrichResult: { ...finding, enriched_at: "2025-02-01T00:00:00Z" },
    })
    vi.stubGlobal("fetch", fetchMock)

    render(<FindingsPage />)

    await waitFor(() => {
      expect(screen.getByText("TLS certificate expired")).toBeInTheDocument()
    })
    // Unenriched rows show a dash in the enriched column.
    expect(screen.getByText("—")).toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: /enriquecer hallazgo/i }))

    await waitFor(() => {
      expect(screen.queryByText("—")).not.toBeInTheDocument()
    })
    const enrichCall = fetchMock.mock.calls.find(
      ([u, o]) => String(u).includes("/enrich") && o?.method === "POST"
    )
    expect(enrichCall).toBeDefined()
  })

  it("downloads a CSV export via blob when the CSV button is clicked", async () => {
    const createObjectURL = vi.fn(() => "blob:fake")
    const revokeObjectURL = vi.fn()
    vi.stubGlobal("URL", { createObjectURL, revokeObjectURL })
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => {})

    const fetchMock = routeFetch({ findings: [finding], assets })
    vi.stubGlobal("fetch", fetchMock)

    render(<FindingsPage />)

    await waitFor(() => {
      expect(screen.getByText("TLS certificate expired")).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole("button", { name: /exportar csv/i }))

    await waitFor(() => {
      expect(createObjectURL).toHaveBeenCalled()
    })
    expect(clickSpy).toHaveBeenCalled()
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:fake")
    const exportCall = fetchMock.mock.calls.find(([u]) =>
      String(u).includes("/asm/export?format=csv")
    )
    expect(exportCall).toBeDefined()
  })

  it("downloads a PDF export via blob when the PDF button is clicked", async () => {
    const createObjectURL = vi.fn(() => "blob:pdf")
    vi.stubGlobal("URL", { createObjectURL, revokeObjectURL: vi.fn() })
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => {})

    const fetchMock = routeFetch({ findings: [finding], assets })
    vi.stubGlobal("fetch", fetchMock)

    render(<FindingsPage />)

    await waitFor(() => {
      expect(screen.getByText("TLS certificate expired")).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole("button", { name: /exportar pdf/i }))

    await waitFor(() => {
      expect(clickSpy).toHaveBeenCalled()
    })
    const exportCall = fetchMock.mock.calls.find(([u]) =>
      String(u).includes("/asm/export?format=pdf")
    )
    expect(exportCall).toBeDefined()
  })

  it("shows an empty state when the tenant has no findings", async () => {
    vi.stubGlobal("fetch", routeFetch({ findings: [], assets }))

    render(<FindingsPage />)

    await waitFor(() => {
      expect(screen.getByText(/sin hallazgos/i)).toBeInTheDocument()
    })
  })

  it("shows an error when findings fail to load", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        if (String(url).includes("/asm/assets")) {
          return Promise.resolve(okJson({ assets }))
        }
        return Promise.resolve({
          ok: false,
          status: 401,
          json: async () => ({ detail: "Not authenticated" }),
        })
      })
    )

    render(<FindingsPage />)

    await waitFor(() => {
      expect(screen.getByText("Not authenticated")).toBeInTheDocument()
    })
  })
})
