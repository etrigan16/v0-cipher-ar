import { afterEach, describe, expect, it, vi } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { WaitlistSection } from "@/components/waitlist"

const okJson = (data: unknown) => ({ ok: true, json: async () => data })
const errJson = (status: number, detail: string) => ({
  ok: false,
  status,
  json: async () => ({ detail }),
})

function getInputs() {
  return {
    email: screen.getByLabelText(/email/i) as HTMLInputElement,
    company: screen.getByLabelText(/company/i) as HTMLInputElement,
    submit: screen.getByRole("button", { name: /join waitlist/i }),
  }
}

describe("WaitlistSection", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("renders email input, company input, and submit button", () => {
    render(<WaitlistSection />)

    const { email, company, submit } = getInputs()
    expect(email).toBeInTheDocument()
    expect(company).toBeInTheDocument()
    expect(submit).toBeInTheDocument()
  })

  it("shows success message after successful API response", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        okJson({ id: "uuid-1", email: "user@example.com", company: null, created_at: "2025-01-01T00:00:00Z" })
      )
    vi.stubGlobal("fetch", fetchMock)

    render(<WaitlistSection />)

    const user = userEvent.setup()
    await user.type(screen.getByLabelText(/email/i), "user@example.com")
    await user.click(screen.getByRole("button", { name: /join waitlist/i }))

    await waitFor(() => {
      expect(screen.getByText(/you're on the list/i)).toBeInTheDocument()
    })
  })

  it("shows inline error on invalid email client-side", async () => {
    render(<WaitlistSection />)

    const emailInput = screen.getByLabelText(/email/i)
    await userEvent.type(emailInput, "not-an-email")

    // Directly submit the form to bypass any HTML5 validation interference
    const form = emailInput.closest("form")!
    fireEvent.submit(form)

    await waitFor(() => {
      expect(screen.getByText(/invalid email format/i)).toBeInTheDocument()
    })
  })

  it("shows error state when API returns a non-OK response", async () => {
    const fetchMock = vi.fn().mockResolvedValue(errJson(429, "Try again later"))
    vi.stubGlobal("fetch", fetchMock)

    render(<WaitlistSection />)

    const user = userEvent.setup()
    await user.type(screen.getByLabelText(/email/i), "existing@example.com")
    await user.click(screen.getByRole("button", { name: /join waitlist/i }))

    await waitFor(() => {
      expect(screen.getByText(/try again later/i)).toBeInTheDocument()
    })
  })
})
