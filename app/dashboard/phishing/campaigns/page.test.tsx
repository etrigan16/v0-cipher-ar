import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import CampaignsPage from "@/app/dashboard/phishing/campaigns/page"

const okJson = (data: unknown) => ({ ok: true, json: async () => data })

const template = {
  id: "tpl-1",
  name: "Banco Aviso",
  subject: "Aviso importante {{nombre}}",
  html_body: "<p>Hola {{nombre}}</p>",
  category: "bank",
  created_at: "2025-01-01T00:00:00Z",
}

const campaign = {
  id: "camp-1",
  name: "Campaña Q1",
  template_id: "tpl-1",
  status: "draft",
  started_at: null,
  completed_at: null,
  created_at: "2025-01-01T00:00:00Z",
  target_count: 0,
}

const target = {
  id: "t-1",
  email: "a@b.com",
  name: "A",
  status: "pending",
  tracking_token: null,
  created_at: "2025-01-01T00:00:00Z",
}

type Handler = (url: string, opts?: RequestInit) => Promise<{ ok: boolean; json: () => Promise<unknown> }>

/** Route-based fetch mock: campaigns list by default, override per URL. */
function routeFetch(overrides: Record<string, Handler> = {}) {
  return vi.fn().mockImplementation((url: string, opts?: RequestInit) => {
    if (url.includes("/phishing/templates")) {
      return Promise.resolve(okJson({ templates: [template] }))
    }
    if (url.includes("/phishing/campaigns")) {
      return Promise.resolve(okJson({ campaigns: [campaign] }))
    }
    return Promise.resolve(okJson({ targets: [target] }))
  })
}

describe("CampaignsPage", () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  it("loads and lists the tenant's campaigns", async () => {
    vi.stubGlobal("fetch", routeFetch())

    render(<CampaignsPage />)

    await waitFor(() => {
      expect(screen.getByText("Campaña Q1")).toBeInTheDocument()
    })
    expect(screen.getByText("draft")).toBeInTheDocument()
  })

  it("shows an empty state when there are no campaigns", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        if (url.includes("/phishing/templates")) {
          return Promise.resolve(okJson({ templates: [template] }))
        }
        return Promise.resolve(okJson({ campaigns: [] }))
      })
    )

    render(<CampaignsPage />)

    await waitFor(() => {
      expect(screen.getByText(/Sin campañas/i)).toBeInTheDocument()
    })
  })

  it("creates a campaign with a name and selected template", async () => {
    let created = false
    const fetchMock = vi.fn().mockImplementation((url: string, opts?: RequestInit) => {
      if (
        url.includes("/phishing/campaigns") &&
        opts?.method === "POST" &&
        !created
      ) {
        created = true
        return Promise.resolve(okJson(campaign))
      }
      if (url.includes("/phishing/templates")) {
        return Promise.resolve(okJson({ templates: [template] }))
      }
      if (url.includes("/targets")) {
        return Promise.resolve(okJson({ targets: [] }))
      }
      if (url.includes("/phishing/campaigns")) {
        return Promise.resolve(okJson({ campaigns: created ? [campaign] : [] }))
      }
      return Promise.resolve(okJson({ targets: [] }))
    })
    vi.stubGlobal("fetch", fetchMock)

    render(<CampaignsPage />)

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /nueva campaña/i })
      ).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole("button", { name: /nueva campaña/i }))

    fireEvent.change(screen.getByLabelText(/nombre de la campaña/i), {
      target: { value: "Campaña Q1" },
    })
    fireEvent.change(screen.getByLabelText(/plantilla/i), {
      target: { value: "tpl-1" },
    })
    fireEvent.click(screen.getByRole("button", { name: /crear campaña/i }))

    await waitFor(() => {
      const createCall = fetchMock.mock.calls.find(
        ([url, opts]) =>
          typeof url === "string" &&
          url.includes("/phishing/campaigns") &&
          (opts as RequestInit)?.method === "POST"
      )
      expect(createCall).toBeDefined()
      const body = JSON.parse((createCall![1] as RequestInit).body as string)
      expect(body).toEqual({ name: "Campaña Q1", template_id: "tpl-1" })
    })

    await waitFor(() => {
      expect(screen.getAllByText("Campaña Q1").length).toBeGreaterThan(0)
    })
  })

  it("uploads a CSV of targets into the selected campaign", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string, opts?: RequestInit) => {
      if (url.includes("/targets/upload")) {
        return Promise.resolve(okJson({ count: 2, targets: [] }))
      }
      if (url.includes("/targets")) {
        return Promise.resolve(okJson({ targets: [] }))
      }
      if (url.includes("/phishing/templates")) {
        return Promise.resolve(okJson({ templates: [template] }))
      }
      return Promise.resolve(okJson({ campaigns: [campaign] }))
    })
    vi.stubGlobal("fetch", fetchMock)

    render(<CampaignsPage />)

    await waitFor(() => {
      expect(screen.getByText("Campaña Q1")).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText("Campaña Q1"))

    const file = new File(["email,name\na@b.com,A\n"], "targets.csv", {
      type: "text/csv",
    })
    const input = screen.getByLabelText(/archivo csv/i) as HTMLInputElement
    fireEvent.change(input, { target: { files: [file] } })

    fireEvent.click(screen.getByRole("button", { name: /subir/i }))

    await waitFor(() => {
      const uploadCall = fetchMock.mock.calls.find(
        ([url, opts]) =>
          typeof url === "string" &&
          url.includes("/camp-1/targets/upload") &&
          (opts as RequestInit)?.method === "POST"
      )
      expect(uploadCall).toBeDefined()
      expect((uploadCall![1] as RequestInit).body).toBeInstanceOf(FormData)
    })

    await waitFor(() => {
      expect(screen.getByText(/2 targets subidos/i)).toBeInTheDocument()
    })
  })

  it("launches a draft campaign and shows the active state", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string, opts?: RequestInit) => {
      if (url.includes("/launch")) {
        return Promise.resolve(
          okJson({
            campaign: { ...campaign, status: "active", target_count: 1 },
            targets: [
              {
                id: "t-1",
                email: "a@b.com",
                name: "A",
                status: "active",
                tracking_token: "tok123",
                landing_url: "https://track.ejemplo.com/l/tok123",
              },
            ],
          })
        )
      }
      if (url.includes("/phishing/templates")) {
        return Promise.resolve(okJson({ templates: [template] }))
      }
      if (url.includes("/targets")) {
        return Promise.resolve(okJson({ targets: [target] }))
      }
      if (url.includes("/phishing/campaigns")) {
        return Promise.resolve(okJson({ campaigns: [campaign] }))
      }
      return Promise.resolve(okJson({ targets: [target] }))
    })
    vi.stubGlobal("fetch", fetchMock)

    render(<CampaignsPage />)

    await waitFor(() => {
      expect(screen.getByText("Campaña Q1")).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText("Campaña Q1"))

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /lanzar/i })).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole("button", { name: /lanzar/i }))

    await waitFor(() => {
      const launchCall = fetchMock.mock.calls.find(
        ([url, opts]) =>
          typeof url === "string" &&
          url.includes("/camp-1/launch") &&
          (opts as RequestInit)?.method === "POST"
      )
      expect(launchCall).toBeDefined()
    })

    await waitFor(() => {
      expect(screen.getByText(/Activa/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/links de distribución/i)).toBeInTheDocument()
  })

  it("cancels an active campaign", async () => {
    const activeCampaign = { ...campaign, status: "active" }
    const fetchMock = vi.fn().mockImplementation((url: string, opts?: RequestInit) => {
      if (url.includes("/cancel")) {
        return Promise.resolve(okJson({ ...activeCampaign, status: "cancelled" }))
      }
      if (url.includes("/phishing/templates")) {
        return Promise.resolve(okJson({ templates: [template] }))
      }
      if (url.includes("/targets")) {
        return Promise.resolve(okJson({ targets: [target] }))
      }
      if (url.includes("/phishing/campaigns")) {
        return Promise.resolve(okJson({ campaigns: [activeCampaign] }))
      }
      return Promise.resolve(okJson({ targets: [target] }))
    })
    vi.stubGlobal("fetch", fetchMock)

    render(<CampaignsPage />)

    await waitFor(() => {
      expect(screen.getByText("Campaña Q1")).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText("Campaña Q1"))

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /cancelar/i })).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole("button", { name: /cancelar/i }))

    await waitFor(() => {
      const cancelCall = fetchMock.mock.calls.find(
        ([url, opts]) =>
          typeof url === "string" &&
          url.includes("/camp-1/cancel") &&
          (opts as RequestInit)?.method === "POST"
      )
      expect(cancelCall).toBeDefined()
    })

    await waitFor(() => {
      expect(screen.getByText(/Cancelada/i)).toBeInTheDocument()
    })
  })

  it("links to the campaign results page", async () => {
    vi.stubGlobal("fetch", routeFetch())

    render(<CampaignsPage />)

    await waitFor(() => {
      expect(screen.getByText("Campaña Q1")).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText("Campaña Q1"))

    const resultsLink = screen.getByRole("link", { name: /ver resultados/i })
    expect(resultsLink).toHaveAttribute(
      "href",
      "/dashboard/phishing/results/camp-1"
    )
  })
})
