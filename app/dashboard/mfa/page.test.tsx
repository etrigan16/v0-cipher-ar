import { type ReactNode } from "react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import MfaPage from "@/app/dashboard/mfa/page"
import { AuthProvider } from "@/components/auth-context"

const okJson = (data: unknown) => ({ ok: true, json: async () => data })

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
  // Pre-set a stored token so AuthProvider loads a session
  localStorage.setItem("token", "test-jwt")
  return render(<AuthProvider>{ui}</AuthProvider>)
}

describe("MfaPage (R7)", () => {
  beforeEach(() => {
    push.mockClear()
    localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("shows setup button when MFA is disabled (R7)", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      okJson({ id: "1", email: "user@example.com", name: "User" }),
    )
    vi.stubGlobal("fetch", fetchMock)

    renderWithAuth(<MfaPage />)

    // Wait for auth to load
    await waitFor(() => {
      expect(screen.getByText(/^MFA Desactivado$/)).toBeInTheDocument()
    })

    // Setup button should be visible
    expect(screen.getByRole("button", { name: /configurar mfa/i })).toBeInTheDocument()
  })

  it("displays QR code and TOTP input after setup (R7)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson({ id: "1", email: "user@example.com", name: "User" }))
      .mockResolvedValueOnce(
        okJson({
          secret: "JBSWY3DPEHPK3PXP",
          provisioning_uri: "otpauth://totp/AUKALABS:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=AUKALABS",
        }),
      )
    vi.stubGlobal("fetch", fetchMock)

    renderWithAuth(<MfaPage />)

    // Wait for auth to load, then click setup
    await waitFor(() => {
      expect(screen.getByText(/MFA Desactivado/i)).toBeInTheDocument()
    })

    await userEvent.click(screen.getByRole("button", { name: /configurar mfa/i }))

    // QR image should appear (from Google Charts API)
    await waitFor(() => {
      const qrImg = screen.getByAltText("QR Code")
      expect(qrImg).toBeInTheDocument()
      expect(qrImg).toHaveAttribute("src", expect.stringContaining("chart.googleapis.com"))
    })

    // Secret should be displayed
    expect(screen.getByText("JBSWY3DPEHPK3PXP")).toBeInTheDocument()

    // TOTP input for verification should be visible
    expect(screen.getByLabelText(/código de verificación/i)).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /verificar y activar/i })).toBeInTheDocument()
  })

  it("shows 'MFA Activado' after successful verification (R7)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson({ id: "1", email: "user@example.com", name: "User" }))
      .mockResolvedValueOnce(
        okJson({
          secret: "JBSWY3DPEHPK3PXP",
          provisioning_uri: "otpauth://totp/AUKALABS:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=AUKALABS",
        }),
      )
      .mockResolvedValueOnce(okJson({ detail: "MFA activado correctamente" }))
    vi.stubGlobal("fetch", fetchMock)

    renderWithAuth(<MfaPage />)

    // Wait for auth, then setup
    await waitFor(() => {
      expect(screen.getByText(/MFA Desactivado/i)).toBeInTheDocument()
    })
    await userEvent.click(screen.getByRole("button", { name: /configurar mfa/i }))

    // Wait for QR / verify section
    await waitFor(() => {
      expect(screen.getByLabelText(/código de verificación/i)).toBeInTheDocument()
    })

    // Enter valid code and verify
    await userEvent.type(screen.getByLabelText(/código de verificación/i), "123456")
    await userEvent.click(screen.getByRole("button", { name: /verificar y activar/i }))

    // Should show MFA enabled status
    await waitFor(() => {
      expect(screen.getByText(/^MFA Activado$/)).toBeInTheDocument()
    })
    expect(screen.getByText("MFA activado correctamente")).toBeInTheDocument()
  })

  it("shows disable form with password confirmation when MFA is enabled (R7)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson({ id: "1", email: "user@example.com", name: "User" }))
      .mockResolvedValueOnce(
        okJson({
          secret: "JBSWY3DPEHPK3PXP",
          provisioning_uri: "otpauth://totp/AUKALABS:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=AUKALABS",
        }),
      )
      .mockResolvedValueOnce(okJson({ detail: "MFA activado correctamente" }))
    vi.stubGlobal("fetch", fetchMock)

    renderWithAuth(<MfaPage />)

    // Setup + verify MFA
    await waitFor(() => expect(screen.getByText(/MFA Desactivado/i)).toBeInTheDocument())
    await userEvent.click(screen.getByRole("button", { name: /configurar mfa/i }))
    await waitFor(() => expect(screen.getByLabelText(/código de verificación/i)).toBeInTheDocument())
    await userEvent.type(screen.getByLabelText(/código de verificación/i), "123456")
    await userEvent.click(screen.getByRole("button", { name: /verificar y activar/i }))

    // Should show disable section with password field
    await waitFor(() => {
      expect(screen.getByText(/^MFA Activado$/)).toBeInTheDocument()
    })
    expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /desactivar mfa/i })).toBeInTheDocument()
  })

  it("disables MFA with correct password (R4 / R7)", async () => {
    const fetchMock = vi
      .fn()
      // auth.me
      .mockResolvedValueOnce(okJson({ id: "1", email: "user@example.com", name: "User" }))
      // setup
      .mockResolvedValueOnce(
        okJson({
          secret: "JBSWY3DPEHPK3PXP",
          provisioning_uri: "otpauth://totp/AUKALABS:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=AUKALABS",
        }),
      )
      // verify
      .mockResolvedValueOnce(okJson({ detail: "MFA activado correctamente" }))
      // disable
      .mockResolvedValueOnce(okJson({ detail: "MFA desactivado correctamente" }))
    vi.stubGlobal("fetch", fetchMock)

    renderWithAuth(<MfaPage />)

    // Setup + verify MFA
    await waitFor(() => expect(screen.getByText(/MFA Desactivado/i)).toBeInTheDocument())
    await userEvent.click(screen.getByRole("button", { name: /configurar mfa/i }))
    await waitFor(() => expect(screen.getByLabelText(/código de verificación/i)).toBeInTheDocument())
    await userEvent.type(screen.getByLabelText(/código de verificación/i), "123456")
    await userEvent.click(screen.getByRole("button", { name: /verificar y activar/i }))

    // Disable MFA
    await waitFor(() => expect(screen.getByText(/^MFA Activado$/)).toBeInTheDocument())
    await userEvent.type(screen.getByLabelText(/contraseña/i), "s3cret")
    await userEvent.click(screen.getByRole("button", { name: /desactivar mfa/i }))

    // Should show MFA disabled status and success message
    await waitFor(() => {
      expect(screen.getByText(/^MFA Desactivado$/)).toBeInTheDocument()
    })
    expect(screen.getByText("MFA desactivado correctamente")).toBeInTheDocument()
  })
})
