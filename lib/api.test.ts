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
