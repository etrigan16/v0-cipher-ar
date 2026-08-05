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

  it("propagates API error detail on non-OK scan response", async () => {
    const fetchMock = vi.fn().mockResolvedValue(errJson(400, "Invalid domain"))
    vi.stubGlobal("fetch", fetchMock)

    await expect(api.asm.scanDomain("bad-domain")).rejects.toThrow("Invalid domain")
  })
})
