import { afterEach, describe, expect, it, vi } from "vitest"
import { api } from "@/lib/api"

const okJson = (data: unknown) => ({ ok: true, json: async () => data })
const errJson = (status: number, detail: string) => ({
  ok: false,
  status,
  json: async () => ({ detail }),
})

describe("api.auth", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  it("login POSTs credentials and returns the access token", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ access_token: "tok-123", token_type: "bearer" }))
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.auth.login("user@example.com", "s3cret")

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/auth/login")
    expect(options.method).toBe("POST")
    expect(options.body).toBe(
      JSON.stringify({ email: "user@example.com", password: "s3cret" })
    )
    expect(res.access_token).toBe("tok-123")
  })

  it("sends the stored token as a Bearer header", async () => {
    localStorage.setItem("token", "jwt-token")
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ id: "1", email: "user@example.com", name: "User" }))
    vi.stubGlobal("fetch", fetchMock)

    await api.auth.me()

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    const headers = options.headers as Record<string, string>
    expect(headers.Authorization).toBe("Bearer jwt-token")
  })

  it("omits the Authorization header when no token is stored", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ id: "1", email: "user@example.com", name: "User" }))
    vi.stubGlobal("fetch", fetchMock)

    await api.auth.me()

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    const headers = options.headers as Record<string, string>
    expect(headers.Authorization).toBeUndefined()
  })

  it("throws the API detail message on non-OK responses", async () => {
    const fetchMock = vi.fn().mockResolvedValue(errJson(401, "Invalid credentials"))
    vi.stubGlobal("fetch", fetchMock)

    await expect(api.auth.login("user@example.com", "wrong")).rejects.toThrow(
      "Invalid credentials"
    )
  })
})

describe("api.waitlist", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  it("submit POSTs email to /waitlist", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        okJson({ id: "uuid-1", email: "user@example.com", company: null, created_at: "2025-01-01T00:00:00Z" })
      )
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.waitlist.submit("user@example.com")

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/waitlist")
    expect(options.method).toBe("POST")
    expect(options.body).toBe(JSON.stringify({ email: "user@example.com", company: undefined }))
    expect(res.id).toBe("uuid-1")
    expect(res.email).toBe("user@example.com")
  })

  it("submit includes optional company in the body", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        okJson({ id: "uuid-2", email: "user@acme.com", company: "Acme Corp", created_at: "2025-01-01T00:00:00Z" })
      )
    vi.stubGlobal("fetch", fetchMock)

    await api.waitlist.submit("user@acme.com", "Acme Corp")

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    const body = JSON.parse(options.body as string)
    expect(body.email).toBe("user@acme.com")
    expect(body.company).toBe("Acme Corp")
  })

  it("throws API error on non-OK response", async () => {
    const fetchMock = vi.fn().mockResolvedValue(errJson(409, "Email already registered"))
    vi.stubGlobal("fetch", fetchMock)

    await expect(api.waitlist.submit("dup@example.com")).rejects.toThrow(
      "Email already registered"
    )
  })
})

describe("api.asm", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  const asset = {
    id: "asset-1",
    domain: "example.com",
    subdomain: "www.example.com",
    ip: "93.184.216.34",
    port: 443,
    service: "https",
    fingerprint: { title: "Example" },
    status: "discovered",
    first_seen: "2025-01-01T00:00:00Z",
    last_seen: "2025-01-01T00:00:00Z",
  }

  it("listAssets GETs /asm/assets and returns typed assets", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ assets: [asset] }))
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.asm.listAssets()

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/asm/assets")
    expect(options.method ?? "GET").toBe("GET")
    expect(res.assets).toHaveLength(1)
    expect(res.assets[0].subdomain).toBe("www.example.com")
  })

  it("scanDomain POSTs {domain} to /asm/scans and returns scan + assets", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      okJson({
        scan: { id: "scan-1", domain: "example.com", status: "complete", started_at: null, completed_at: null, created_at: "2025-01-01T00:00:00Z" },
        assets: [asset],
      })
    )
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.asm.scanDomain("example.com")

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/asm/scans")
    expect(options.method).toBe("POST")
    expect(options.body).toBe(JSON.stringify({ domain: "example.com" }))
    expect(res.scan.status).toBe("complete")
    expect(res.assets[0].ip).toBe("93.184.216.34")
  })

  it("getResults GETs /asm/results/{id} and returns scan + findings", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      okJson({
        scan: { id: "scan-1", domain: "example.com", status: "complete", started_at: null, completed_at: null, created_at: "2025-01-01T00:00:00Z" },
        findings: [{ id: "f-1", asset_id: "asset-1", severity: "low", title: "TLS expired", detail: null, discovered_at: "2025-01-01T00:00:00Z" }],
      })
    )
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.asm.getResults("scan-1")

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/asm/results/scan-1")
    expect(options.method ?? "GET").toBe("GET")
    expect(res.findings[0].severity).toBe("low")
  })

  it("getStats GETs /asm/stats and returns tenant counts", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ assets: 3, findings: 2, scans: 1 }))
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.asm.getStats()

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/asm/stats")
    expect(options.method ?? "GET").toBe("GET")
    expect(res).toEqual({ assets: 3, findings: 2, scans: 1 })
  })

  it("propagates API error detail on non-OK scan response", async () => {
    const fetchMock = vi.fn().mockResolvedValue(errJson(400, "Invalid domain"))
    vi.stubGlobal("fetch", fetchMock)

    await expect(api.asm.scanDomain("bad-domain")).rejects.toThrow("Invalid domain")
  })
})

describe("api.asm risk endpoints", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  const asset = {
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
  }

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

  it("getFindings GETs /asm/findings and returns the typed list", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ findings: [finding], total: 1, limit: 100, offset: 0 }))
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.asm.getFindings()

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/asm/findings")
    expect(options.method ?? "GET").toBe("GET")
    expect(res.findings).toHaveLength(1)
    expect(res.findings[0].risk_score).toBe(9.5)
    expect(res.findings[0].risk_level).toBe("critical")
    expect(res.findings[0].status).toBe("open")
  })

  it("getFindings serializes provided filters as query params", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ findings: [], total: 0, limit: 100, offset: 0 }))
    vi.stubGlobal("fetch", fetchMock)

    await api.asm.getFindings({ severity: "high", status: "open", limit: 25 })

    const [url] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/asm/findings?severity=high&status=open&limit=25")
  })

  it("getFindings omits query params when no filters are given", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ findings: [], total: 0, limit: 100, offset: 0 }))
    vi.stubGlobal("fetch", fetchMock)

    await api.asm.getFindings()

    const [url] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).not.toContain("?")
  })

  it("getRiskSummary GETs /asm/risk-summary and returns metrics + top findings", async () => {
    const summary = {
      severity_counts: { info: 0, low: 1, medium: 2, high: 1, critical: 0 },
      avg_risk: 4.5,
      max_risk: 9.5,
      open_findings: 4,
      top_findings: [finding],
    }
    const fetchMock = vi.fn().mockResolvedValue(okJson(summary))
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.asm.getRiskSummary()

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/asm/risk-summary")
    expect(options.method ?? "GET").toBe("GET")
    expect(res.severity_counts.medium).toBe(2)
    expect(res.avg_risk).toBe(4.5)
    expect(res.max_risk).toBe(9.5)
    expect(res.open_findings).toBe(4)
    expect(res.top_findings[0].title).toBe("TLS certificate expired")
  })

  it("getAsset GETs /asm/assets/{id} and returns the asset with its findings", async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ asset, findings: [finding] }))
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.asm.getAsset("asset-1")

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/asm/assets/asset-1")
    expect(options.method ?? "GET").toBe("GET")
    expect(res.asset.id).toBe("asset-1")
    expect(res.findings[0].status).toBe("open")
  })

  it("patchFinding PATCHes {status} to /asm/findings/{id}", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ ...finding, status: "resolved" }))
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.asm.patchFinding("f-1", "resolved")

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/asm/findings/f-1")
    expect(options.method).toBe("PATCH")
    expect(options.body).toBe(JSON.stringify({ status: "resolved" }))
    expect(res.status).toBe("resolved")
  })

  it("enrichFinding POSTs to /asm/findings/{id}/enrich", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ ...finding, enriched_at: "2025-02-01T00:00:00Z" }))
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.asm.enrichFinding("f-1")

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/asm/findings/f-1/enrich")
    expect(options.method).toBe("POST")
    expect(res.enriched_at).toBe("2025-02-01T00:00:00Z")
  })

  it("exportFindings GETs /asm/export?format=csv and resolves a Blob", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue({
        ok: true,
        blob: async () => new Blob(["a,b\n"], { type: "text/csv" }),
      })
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.asm.exportFindings("csv")

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/asm/export?format=csv")
    expect(options.method ?? "GET").toBe("GET")
    expect(res).toBeInstanceOf(Blob)
  })

  it("exportFindings accepts the pdf format", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue({
        ok: true,
        blob: async () => new Blob(["%PDF"], { type: "application/pdf" }),
      })
    vi.stubGlobal("fetch", fetchMock)

    await api.asm.exportFindings("pdf")

    const [url] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/asm/export?format=pdf")
  })

  it("exportFindings sends the stored token as a Bearer header", async () => {
    localStorage.setItem("token", "jwt-token")
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, blob: async () => new Blob(["x"]) })
    vi.stubGlobal("fetch", fetchMock)

    await api.asm.exportFindings("csv")

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    const headers = options.headers as Record<string, string>
    expect(headers.Authorization).toBe("Bearer jwt-token")
  })

  it("exportFindings throws the API detail on non-OK responses", async () => {
    const fetchMock = vi.fn().mockResolvedValue(errJson(401, "Not authenticated"))
    vi.stubGlobal("fetch", fetchMock)

    await expect(api.asm.exportFindings("csv")).rejects.toThrow("Not authenticated")
  })

  it("patchFinding propagates API error detail on non-OK responses", async () => {
    const fetchMock = vi.fn().mockResolvedValue(errJson(422, "Invalid status"))
    vi.stubGlobal("fetch", fetchMock)

    await expect(api.asm.patchFinding("f-1", "resolved")).rejects.toThrow(
      "Invalid status"
    )
  })
})

describe("api.phishing templates", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  const template = {
    id: "tpl-1",
    name: "Banco Aviso",
    subject: "Aviso importante {{nombre}}",
    html_body:
      "<p>Hola {{nombre}}, su cuenta {{empresa}} necesita atencion: {{link}}</p>",
    category: "bank",
    created_at: "2025-01-01T00:00:00Z",
  }

  it("listTemplates GETs /phishing/templates and returns typed templates", async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ templates: [template] }))
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.phishing.listTemplates()

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/phishing/templates")
    expect(options.method ?? "GET").toBe("GET")
    expect(res.templates).toHaveLength(1)
    expect(res.templates[0].category).toBe("bank")
    expect(res.templates[0].subject).toContain("{{nombre}}")
  })

  it("createTemplate POSTs the payload and returns the created template", async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson(template))
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.phishing.createTemplate({
      name: "Banco Aviso",
      subject: "Aviso importante {{nombre}}",
      html_body: "<p>Hola {{nombre}}</p>",
      category: "bank",
    })

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/phishing/templates")
    expect(options.method).toBe("POST")
    expect(options.body).toBe(
      JSON.stringify({
        name: "Banco Aviso",
        subject: "Aviso importante {{nombre}}",
        html_body: "<p>Hola {{nombre}}</p>",
        category: "bank",
      })
    )
    expect(res.id).toBe("tpl-1")
  })

  it("updateTemplate PUTs to /phishing/templates/{id}", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ ...template, subject: "Nuevo asunto" }))
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.phishing.updateTemplate("tpl-1", {
      name: "Banco Aviso",
      subject: "Nuevo asunto",
      html_body: "<p>nuevo</p>",
      category: "bank",
    })

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/phishing/templates/tpl-1")
    expect(options.method).toBe("PUT")
    expect(res.subject).toBe("Nuevo asunto")
  })

  it("deleteTemplate DELETEs /phishing/templates/{id} and resolves on 204", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
      json: async () => {
        throw new Error("no body expected")
      },
    })
    vi.stubGlobal("fetch", fetchMock)

    await expect(api.phishing.deleteTemplate("tpl-1")).resolves.toBeUndefined()

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/phishing/templates/tpl-1")
    expect(options.method).toBe("DELETE")
  })

  it("deleteTemplate propagates API error detail on non-OK responses", async () => {
    const fetchMock = vi.fn().mockResolvedValue(errJson(404, "Template not found"))
    vi.stubGlobal("fetch", fetchMock)

    await expect(api.phishing.deleteTemplate("missing")).rejects.toThrow(
      "Template not found"
    )
  })
})

describe("api.phishing campaigns", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

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

  it("listCampaigns GETs /phishing/campaigns and returns typed campaigns", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ campaigns: [campaign] }))
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.phishing.listCampaigns()

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/phishing/campaigns")
    expect(options.method ?? "GET").toBe("GET")
    expect(res.campaigns).toHaveLength(1)
    expect(res.campaigns[0].status).toBe("draft")
  })

  it("createCampaign POSTs {name, template_id} and returns the campaign", async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson(campaign))
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.phishing.createCampaign({
      name: "Campaña Q1",
      template_id: "tpl-1",
    })

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/phishing/campaigns")
    expect(options.method).toBe("POST")
    expect(options.body).toBe(
      JSON.stringify({ name: "Campaña Q1", template_id: "tpl-1" })
    )
    expect(res.id).toBe("camp-1")
  })

  it("uploadTargets sends the CSV file as multipart FormData", async () => {
    const file = new File(["email,name\na@b.com,A\n"], "targets.csv", {
      type: "text/csv",
    })
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ count: 1, targets: [] }))
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.phishing.uploadTargets("camp-1", file)

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/phishing/campaigns/camp-1/targets/upload")
    expect(options.method).toBe("POST")
    expect(options.body).toBeInstanceOf(FormData)
    expect(res.count).toBe(1)
  })

  it("uploadTargets sends the stored token as a Bearer header", async () => {
    localStorage.setItem("token", "jwt-token")
    const file = new File(["email,name\n"], "targets.csv", { type: "text/csv" })
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ count: 0, targets: [] }))
    vi.stubGlobal("fetch", fetchMock)

    await api.phishing.uploadTargets("camp-1", file)

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    const headers = options.headers as Record<string, string>
    expect(headers.Authorization).toBe("Bearer jwt-token")
  })

  it("launchCampaign POSTs to /phishing/campaigns/{id}/launch and returns links", async () => {
    const launch = {
      campaign: { ...campaign, status: "active" },
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
    }
    const fetchMock = vi.fn().mockResolvedValue(okJson(launch))
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.phishing.launchCampaign("camp-1")

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/phishing/campaigns/camp-1/launch")
    expect(options.method).toBe("POST")
    expect(res.campaign.status).toBe("active")
    expect(res.targets[0].landing_url).toContain("/l/tok123")
  })

  it("cancelCampaign POSTs to /phishing/campaigns/{id}/cancel", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ ...campaign, status: "cancelled" }))
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.phishing.cancelCampaign("camp-1")

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/phishing/campaigns/camp-1/cancel")
    expect(options.method).toBe("POST")
    expect(res.status).toBe("cancelled")
  })
})

describe("api.phishing results", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  const targetResult = {
    email: "a@b.com",
    name: "A",
    status: "active",
    opened: true,
    opened_at: "2025-01-01T00:00:00Z",
    clicked: false,
    clicked_at: null,
    credential: false,
    credential_at: null,
    reported: false,
    reported_at: null,
  }

  it("getCampaignResults GETs /phishing/campaigns/{id}/results", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ campaign_id: "camp-1", targets: [targetResult] }))
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.phishing.getCampaignResults("camp-1")

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/phishing/campaigns/camp-1/results")
    expect(options.method ?? "GET").toBe("GET")
    expect(res.campaign_id).toBe("camp-1")
    expect(res.targets[0].opened).toBe(true)
  })

  it("getResultsSummary GETs /phishing/results-summary and returns rates", async () => {
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
    const fetchMock = vi.fn().mockResolvedValue(okJson(summary))
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.phishing.getResultsSummary()

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/phishing/results-summary")
    expect(options.method ?? "GET").toBe("GET")
    expect(res.opened_rate).toBe(40.0)
    expect(res.sent).toBe(10)
  })

  it("exportCampaign GETs /phishing/campaigns/{id}/export?format=csv and resolves a Blob", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      blob: async () => new Blob(["email,name\n"], { type: "text/csv" }),
    })
    vi.stubGlobal("fetch", fetchMock)

    const res = await api.phishing.exportCampaign("camp-1", "csv")

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/phishing/campaigns/camp-1/export?format=csv")
    expect(options.method ?? "GET").toBe("GET")
    expect(res).toBeInstanceOf(Blob)
  })

  it("exportCampaign accepts the pdf format", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      blob: async () => new Blob(["%PDF"], { type: "application/pdf" }),
    })
    vi.stubGlobal("fetch", fetchMock)

    await api.phishing.exportCampaign("camp-1", "pdf")

    const [url] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/phishing/campaigns/camp-1/export?format=pdf")
  })

  it("exportCampaign throws the API detail on non-OK responses", async () => {
    const fetchMock = vi.fn().mockResolvedValue(errJson(404, "Campaign not found"))
    vi.stubGlobal("fetch", fetchMock)

    await expect(api.phishing.exportCampaign("nope", "csv")).rejects.toThrow(
      "Campaign not found"
    )
  })
})
