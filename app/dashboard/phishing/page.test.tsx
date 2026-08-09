import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import PhishingHubPage from "@/app/dashboard/phishing/page"

describe("PhishingHubPage", () => {
  it("links to the templates, campaigns and results sub-pages", () => {
    render(<PhishingHubPage />)

    expect(screen.getByRole("link", { name: /plantillas/i })).toHaveAttribute(
      "href",
      "/dashboard/phishing/templates"
    )
    const campaignLinks = screen.getAllByRole("link", { name: /campañas/i })
    expect(campaignLinks.length).toBeGreaterThan(0)
    expect(
      campaignLinks.some((l) => l.getAttribute("href") === "/dashboard/phishing/campaigns")
    ).toBe(true)
    expect(screen.getByRole("link", { name: /resultados/i })).toHaveAttribute(
      "href",
      "/dashboard/phishing/results"
    )
  })
})
