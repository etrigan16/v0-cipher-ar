import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import TemplatesPage from "@/app/dashboard/phishing/templates/page"

const okJson = (data: unknown) => ({ ok: true, json: async () => data })

const template = {
  id: "tpl-1",
  name: "Banco Aviso",
  subject: "Aviso importante {{nombre}}",
  html_body: "<p>Hola {{nombre}} de {{empresa}}: {{link}}</p>",
  category: "bank",
  created_at: "2025-01-01T00:00:00Z",
}

describe("TemplatesPage", () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  it("loads and lists the tenant's templates", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(okJson({ templates: [template] }))
    )

    render(<TemplatesPage />)

    await waitFor(() => {
      expect(screen.getByText("Banco Aviso")).toBeInTheDocument()
    })
    expect(screen.getByText("Aviso importante {{nombre}}")).toBeInTheDocument()
    expect(screen.getByText("bank")).toBeInTheDocument()
  })

  it("shows an empty state when there are no templates", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(okJson({ templates: [] })))

    render(<TemplatesPage />)

    await waitFor(() => {
      expect(screen.getByText(/Sin plantillas/i)).toBeInTheDocument()
    })
  })

  it("shows an error when templates fail to load", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ detail: "Not authenticated" }),
      })
    )

    render(<TemplatesPage />)

    await waitFor(() => {
      expect(screen.getByText("Not authenticated")).toBeInTheDocument()
    })
  })

  it("creates a template from the structured editor", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson({ templates: [] }))
      .mockResolvedValueOnce(okJson({ ...template, id: "tpl-new" }))
      .mockResolvedValueOnce(okJson({ templates: [{ ...template, id: "tpl-new" }] }))
    vi.stubGlobal("fetch", fetchMock)

    render(<TemplatesPage />)

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /nueva plantilla/i })
      ).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole("button", { name: /nueva plantilla/i }))

    fireEvent.change(screen.getByLabelText(/nombre de la plantilla/i), {
      target: { value: "Banco Aviso" },
    })
    fireEvent.change(screen.getByLabelText(/asunto/i), {
      target: { value: "Aviso importante {{nombre}}" },
    })
    fireEvent.change(screen.getByLabelText(/cuerpo html/i), {
      target: { value: "<p>Hola {{nombre}}</p>" },
    })
    fireEvent.change(screen.getByLabelText(/categoría/i), {
      target: { value: "bank" },
    })
    fireEvent.click(screen.getByRole("button", { name: /guardar/i }))

    await waitFor(() => {
      const createCall = fetchMock.mock.calls.find(
        ([url, opts]) =>
          typeof url === "string" &&
          url.includes("/phishing/templates") &&
          (opts as RequestInit)?.method === "POST"
      )
      expect(createCall).toBeDefined()
    })

    await waitFor(() => {
      expect(screen.getByText("Banco Aviso")).toBeInTheDocument()
    })
  })

  it("deletes a template and refreshes the list", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson({ templates: [template] }))
      .mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: async () => {
          throw new Error("no body")
        },
      })
      .mockResolvedValueOnce(okJson({ templates: [] }))
    vi.stubGlobal("fetch", fetchMock)

    render(<TemplatesPage />)

    await waitFor(() => {
      expect(screen.getByText("Banco Aviso")).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole("button", { name: /eliminar/i }))

    await waitFor(() => {
      const deleteCall = fetchMock.mock.calls.find(
        ([url, opts]) =>
          typeof url === "string" &&
          url.includes("/phishing/templates/tpl-1") &&
          (opts as RequestInit)?.method === "DELETE"
      )
      expect(deleteCall).toBeDefined()
    })

    await waitFor(() => {
      expect(screen.queryByText("Banco Aviso")).not.toBeInTheDocument()
    })
  })

  it("inserts a variable chip at the cursor in the body", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(okJson({ templates: [] })))

    render(<TemplatesPage />)

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /nueva plantilla/i })
      ).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole("button", { name: /nueva plantilla/i }))

    const body = screen.getByLabelText(/cuerpo html/i) as HTMLTextAreaElement
    fireEvent.change(body, { target: { value: "Hola " } })
    body.setSelectionRange(5, 5)
    fireEvent.click(screen.getByRole("button", { name: "{{nombre}}" }))

    expect(body.value).toBe("Hola {{nombre}}")
  })

  it("toggles to live preview showing sample values", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(okJson({ templates: [] })))

    render(<TemplatesPage />)

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /nueva plantilla/i })
      ).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole("button", { name: /nueva plantilla/i }))

    fireEvent.change(screen.getByLabelText(/cuerpo html/i), {
      target: { value: "<p>Hola {{nombre}} de {{empresa}}</p>" },
    })
    fireEvent.click(screen.getByRole("button", { name: /vista previa/i }))

    await waitFor(() => {
      expect(screen.getByText(/María Pérez/)).toBeInTheDocument()
    })
    expect(screen.getByText(/Acme S.A./)).toBeInTheDocument()
  })

  it("source toggle round-trips back to the raw HTML", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(okJson({ templates: [] })))

    render(<TemplatesPage />)

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /nueva plantilla/i })
      ).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole("button", { name: /nueva plantilla/i }))

    const raw = "<p>Hola {{nombre}}</p>"
    fireEvent.change(screen.getByLabelText(/cuerpo html/i), {
      target: { value: raw },
    })
    fireEvent.click(screen.getByRole("button", { name: /vista previa/i }))
    await waitFor(() => {
      expect(screen.queryByLabelText(/cuerpo html/i)).not.toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole("button", { name: /fuente/i }))
    const body = screen.getByLabelText(/cuerpo html/i) as HTMLTextAreaElement
    expect(body.value).toBe(raw)
  })
})
