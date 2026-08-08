import { describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import DashboardLayout from "@/app/dashboard/layout"

vi.mock("@/components/auth-context", () => ({
  useAuth: () => ({
    user: {
      id: "1",
      email: "user@example.com",
      name: "Test User",
      tenant: { id: "t-1", slug: "acme" },
    },
    loading: false,
    logout: vi.fn(),
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
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

describe("DashboardLayout sidebar", () => {
  it("renders a Findings nav link pointing at /dashboard/findings", () => {
    render(
      <DashboardLayout>
        <div>page content</div>
      </DashboardLayout>
    )

    const findingsLink = screen.getByRole("link", { name: /findings/i })
    expect(findingsLink).toHaveAttribute("href", "/dashboard/findings")
  })

  it("keeps the existing dashboard, attack-surface and phishing links", () => {
    render(
      <DashboardLayout>
        <div>page content</div>
      </DashboardLayout>
    )

    expect(screen.getByRole("link", { name: /dashboard/i })).toHaveAttribute(
      "href",
      "/dashboard"
    )
    expect(screen.getByRole("link", { name: /attack surface/i })).toHaveAttribute(
      "href",
      "/dashboard/attack-surface"
    )
    expect(screen.getByRole("link", { name: /phishing/i })).toHaveAttribute(
      "href",
      "/dashboard/phishing"
    )
  })
})
