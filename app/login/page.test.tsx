import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import LoginPage from "@/app/login/page"

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

describe("LoginPage", () => {
  beforeEach(() => {
    push.mockClear()
    localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("redirects to /dashboard after a successful login", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ access_token: "tok-123", token_type: "bearer" }),
    })
    vi.stubGlobal("fetch", fetchMock)

    render(<LoginPage />)

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

    render(<LoginPage />)

    await userEvent.type(screen.getByLabelText(/email/i), "user@example.com")
    await userEvent.type(screen.getByLabelText(/password/i), "wrong")
    await userEvent.click(screen.getByRole("button", { name: /iniciar sesión/i }))

    await waitFor(() =>
      expect(screen.getByText("Invalid credentials")).toBeInTheDocument()
    )
    expect(push).not.toHaveBeenCalled()
    expect(localStorage.getItem("token")).toBeNull()
  })
})
