import { type ReactNode } from "react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import LoginPage from "@/app/login/page"
import { AuthProvider } from "@/components/auth-context"

const { push } = vi.hoisted(() => ({ push: vi.fn() }))

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}))

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...props
  }: {
    href: string
    children: React.ReactNode
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}))

function renderWithAuth(ui: ReactNode) {
  return render(<AuthProvider>{ui}</AuthProvider>)
}

describe("LoginPage", () => {
  beforeEach(() => {
    push.mockClear()
    localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("redirects to /dashboard after a successful login (MFA disabled)", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ access_token: "tok-123", token_type: "bearer" }),
    })
    vi.stubGlobal("fetch", fetchMock)

    renderWithAuth(<LoginPage />)

    await userEvent.type(screen.getByLabelText(/email/i), "user@example.com")
    await userEvent.type(screen.getByLabelText(/password/i), "s3cret")
    await userEvent.click(screen.getByRole("button", { name: /iniciar sesión/i }))

    await waitFor(() => expect(push).toHaveBeenCalledWith("/dashboard"))
    expect(localStorage.getItem("token")).toBe("tok-123")
  })

  it("shows the error message and stays on the page when login fails", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Invalid credentials" }),
    })
    vi.stubGlobal("fetch", fetchMock)

    renderWithAuth(<LoginPage />)

    await userEvent.type(screen.getByLabelText(/email/i), "user@example.com")
    await userEvent.type(screen.getByLabelText(/password/i), "wrong")
    await userEvent.click(screen.getByRole("button", { name: /iniciar sesión/i }))

    await waitFor(() =>
      expect(screen.getByText("Invalid credentials")).toBeInTheDocument()
    )
    expect(push).not.toHaveBeenCalled()
    expect(localStorage.getItem("token")).toBeNull()
  })

  // ── R8: MFA TOTP step ──────────────────────────────────────────────────

  it("shows TOTP input when login returns mfa_required: true (R8)", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        partial_token: "partial-jwt",
        token_type: "bearer",
        mfa_required: true,
      }),
    })
    vi.stubGlobal("fetch", fetchMock)

    renderWithAuth(<LoginPage />)

    // Initial state shows email/password form
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()

    await userEvent.type(screen.getByLabelText(/email/i), "mfa-user@example.com")
    await userEvent.type(screen.getByLabelText(/password/i), "s3cret")
    await userEvent.click(screen.getByRole("button", { name: /iniciar sesión/i }))

    // After MFA response, TOTP input should appear
    await waitFor(() => {
      expect(screen.getByLabelText(/código totp/i)).toBeInTheDocument()
    })

    // Should NOT redirect — still in MFA step
    expect(push).not.toHaveBeenCalled()
  })

  it("stores full JWT on successful TOTP challenge (R8)", async () => {
    // First call: login returns partial_token + mfa_required
    // Second call: challenge succeeds and returns access_token
    // Third call: /auth/me after challenge (inside completeMfaChallenge)
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          partial_token: "partial-jwt",
          token_type: "bearer",
          mfa_required: true,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ access_token: "full-jwt", token_type: "bearer" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: "1", email: "mfa-user@example.com", name: "User" }),
      })
    vi.stubGlobal("fetch", fetchMock)

    renderWithAuth(<LoginPage />)

    await userEvent.type(screen.getByLabelText(/email/i), "mfa-user@example.com")
    await userEvent.type(screen.getByLabelText(/password/i), "s3cret")
    await userEvent.click(screen.getByRole("button", { name: /iniciar sesión/i }))

    // Wait for TOTP input to appear
    await waitFor(() => {
      expect(screen.getByLabelText(/código totp/i)).toBeInTheDocument()
    })

    // Enter valid TOTP code
    const totpInput = screen.getByLabelText(/código totp/i)
    await userEvent.type(totpInput, "123456")

    await userEvent.click(screen.getByRole("button", { name: /verificar código/i }))

    // Should store full JWT and redirect to dashboard
    await waitFor(() => {
      expect(localStorage.getItem("token")).toBe("full-jwt")
    })
    expect(push).toHaveBeenCalledWith("/dashboard")
  })

  it("shows error message on failed TOTP challenge (R8)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          partial_token: "partial-jwt",
          token_type: "bearer",
          mfa_required: true,
        }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: "Código inválido" }),
      })
    vi.stubGlobal("fetch", fetchMock)

    renderWithAuth(<LoginPage />)

    await userEvent.type(screen.getByLabelText(/email/i), "mfa-user@example.com")
    await userEvent.type(screen.getByLabelText(/password/i), "s3cret")
    await userEvent.click(screen.getByRole("button", { name: /iniciar sesión/i }))

    // Wait for TOTP input
    await waitFor(() => {
      expect(screen.getByLabelText(/código totp/i)).toBeInTheDocument()
    })

    // Enter invalid code
    await userEvent.type(screen.getByLabelText(/código totp/i), "000000")
    await userEvent.click(screen.getByRole("button", { name: /verificar código/i }))

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText("Código inválido")).toBeInTheDocument()
    })

    // Should NOT store token and NOT redirect
    expect(localStorage.getItem("token")).toBeNull()
    expect(push).not.toHaveBeenCalledWith("/dashboard")

    // User should still be on the TOTP step (can retry)
    expect(screen.getByLabelText(/código totp/i)).toBeInTheDocument()
  })

  it("allows going back to email/password form from TOTP step (R8)", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        partial_token: "partial-jwt",
        token_type: "bearer",
        mfa_required: true,
      }),
    })
    vi.stubGlobal("fetch", fetchMock)

    renderWithAuth(<LoginPage />)

    await userEvent.type(screen.getByLabelText(/email/i), "mfa-user@example.com")
    await userEvent.type(screen.getByLabelText(/password/i), "s3cret")
    await userEvent.click(screen.getByRole("button", { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(screen.getByLabelText(/código totp/i)).toBeInTheDocument()
    })

    // Click "Volver al inicio de sesión"
    await userEvent.click(screen.getByRole("button", { name: /volver al inicio/i }))

    // Should show email form again
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
  })
})
