import { afterEach, describe, expect, it, vi } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { AuthProvider, useAuth } from "@/components/auth-context"

const okJson = (data: unknown) => ({ ok: true, json: async () => data })

function Probe() {
  const { user, token, loading, login, logout } = useAuth()
  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="user">{user?.email ?? "none"}</span>
      <span data-testid="token">{token ?? "none"}</span>
      <button onClick={() => login("user@example.com", "s3cret")}>login</button>
      <button onClick={logout}>logout</button>
    </div>
  )
}

describe("AuthProvider", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  it("restores the session from localStorage on mount", async () => {
    localStorage.setItem("token", "stored-token")
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ id: "1", email: "user@example.com", name: "User" }))
    vi.stubGlobal("fetch", fetchMock)

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    )

    await waitFor(() =>
      expect(screen.getByTestId("user").textContent).toBe("user@example.com")
    )
    expect(screen.getByTestId("token").textContent).toBe("stored-token")
    expect(screen.getByTestId("loading").textContent).toBe("false")
  })

  it("logs in, persists the token, and loads the profile", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson({ access_token: "fresh-token", token_type: "bearer" }))
      .mockResolvedValueOnce(okJson({ id: "2", email: "user@example.com", name: "User" }))
    vi.stubGlobal("fetch", fetchMock)

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    )

    await userEvent.click(screen.getByRole("button", { name: "login" }))

    await waitFor(() => expect(screen.getByTestId("token").textContent).toBe("fresh-token"))
    expect(localStorage.getItem("token")).toBe("fresh-token")
    expect(screen.getByTestId("user").textContent).toBe("user@example.com")
  })

  it("logs out and clears the session", async () => {
    localStorage.setItem("token", "stored-token")
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson({ id: "1", email: "user@example.com", name: "User" }))
    vi.stubGlobal("fetch", fetchMock)

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    )
    await waitFor(() =>
      expect(screen.getByTestId("user").textContent).toBe("user@example.com")
    )

    await userEvent.click(screen.getByRole("button", { name: "logout" }))

    expect(screen.getByTestId("token").textContent).toBe("none")
    expect(screen.getByTestId("user").textContent).toBe("none")
    expect(localStorage.getItem("token")).toBeNull()
  })

  it("drops an invalid stored token when the profile request fails", async () => {
    localStorage.setItem("token", "expired-token")
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Unauthorized" }),
    })
    vi.stubGlobal("fetch", fetchMock)

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    )

    await waitFor(() => expect(screen.getByTestId("loading").textContent).toBe("false"))
    expect(localStorage.getItem("token")).toBeNull()
    expect(screen.getByTestId("token").textContent).toBe("none")
  })
})
