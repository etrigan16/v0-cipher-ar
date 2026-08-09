"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { Code2, Eye, FileText, Loader2, Pencil, Plus, Trash2 } from "lucide-react"
import { api, type Template, type TemplateCategory } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

/** Template variables (spec R4) — the chips insert these at the cursor. */
export const TEMPLATE_VARIABLES = ["{{nombre}}", "{{empresa}}", "{{link}}"] as const

/** Sample values used by the live preview (spec R5). */
export const PREVIEW_SAMPLE = {
  nombre: "María Pérez",
  empresa: "Acme S.A.",
  link: "https://acme.ejemplo.com/l/abc123",
}

const CATEGORY_LABELS: Record<TemplateCategory, string> = {
  bank: "Banco",
  government: "Gobierno",
  tech: "Tecnología",
}

const CATEGORY_OPTIONS: TemplateCategory[] = ["bank", "government", "tech"]

const EMPTY_FORM = { name: "", subject: "", html_body: "", category: "bank" as TemplateCategory }

/** Replace the three template variables with sample values for the preview. */
export function renderPreview(html: string): string {
  return html
    .replaceAll("{{nombre}}", PREVIEW_SAMPLE.nombre)
    .replaceAll("{{empresa}}", PREVIEW_SAMPLE.empresa)
    .replaceAll("{{link}}", PREVIEW_SAMPLE.link)
}

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Editor state: null = list view; { template } = editing; {} = creating.
  const [editing, setEditing] = useState<Template | null | undefined>(undefined)
  const [form, setForm] = useState(EMPTY_FORM)
  const [view, setView] = useState<"source" | "preview">("source")
  const [saving, setSaving] = useState(false)
  const bodyRef = useRef<HTMLTextAreaElement>(null)

  const refresh = useCallback(async () => {
    try {
      const res = await api.phishing.listTemplates()
      setTemplates(res.templates)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron cargar las plantillas")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let active = true
    api.phishing
      .listTemplates()
      .then((res) => {
        if (active) {
          setTemplates(res.templates)
          setError(null)
        }
      })
      .catch((e) => {
        if (active) {
          setError(e instanceof Error ? e.message : "No se pudieron cargar las plantillas")
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  const openCreate = () => {
    setEditing(null)
    setForm(EMPTY_FORM)
    setView("source")
  }

  const openEdit = (t: Template) => {
    setEditing(t)
    setForm({
      name: t.name,
      subject: t.subject,
      html_body: t.html_body,
      category: t.category,
    })
    setView("source")
  }

  const closeEditor = () => {
    setEditing(undefined)
  }

  /** Insert a variable chip at the cursor (or at the end) of the body. */
  const insertVariable = (variable: string) => {
    const el = bodyRef.current
    if (!el) return
    const start = el.selectionStart ?? form.html_body.length
    const end = el.selectionEnd ?? start
    const next = form.html_body.slice(0, start) + variable + form.html_body.slice(end)
    setForm((prev) => ({ ...prev, html_body: next }))
    requestAnimationFrame(() => {
      el.focus()
      el.setSelectionRange(start + variable.length, start + variable.length)
    })
  }

  const save = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name.trim() || !form.subject.trim() || !form.html_body.trim()) {
      setError("Nombre, asunto y cuerpo HTML son obligatorios")
      return
    }
    setSaving(true)
    setError(null)
    try {
      const payload = {
        name: form.name.trim(),
        subject: form.subject.trim(),
        html_body: form.html_body,
        category: form.category,
      }
      if (editing) {
        await api.phishing.updateTemplate(editing.id, payload)
      } else {
        await api.phishing.createTemplate(payload)
      }
      setEditing(undefined)
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo guardar la plantilla")
    } finally {
      setSaving(false)
    }
  }

  const remove = async (t: Template) => {
    setError(null)
    try {
      await api.phishing.deleteTemplate(t.id)
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo eliminar la plantilla")
    }
  }

  return (
    <div>
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-mono text-2xl font-bold">
            PLANTILLAS<span className="text-primary">_</span>
          </h1>
          <p className="font-mono text-sm text-muted-foreground mt-1">
            Plantillas de phishing con variables para cada destinatario
          </p>
        </div>
        {editing === undefined && (
          <Button onClick={openCreate}>
            <Plus size={16} />
            Nueva plantilla
          </Button>
        )}
      </div>

      {error && (
        <div role="alert" className="border border-destructive bg-card p-4 mb-6">
          <p className="font-mono text-sm text-destructive">{error}</p>
        </div>
      )}

      {editing !== undefined && (
        <form
          onSubmit={save}
          className="border border-border bg-card p-6 mb-8 space-y-4"
        >
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="tpl-name">Nombre de la plantilla</Label>
              <Input
                id="tpl-name"
                value={form.name}
                onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
                placeholder="ej: Alerta de seguridad bancaria"
                aria-label="Nombre de la plantilla"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="tpl-category">Categoría</Label>
              <select
                id="tpl-category"
                aria-label="Categoría"
                value={form.category}
                onChange={(e) =>
                  setForm((p) => ({
                    ...p,
                    category: e.target.value as TemplateCategory,
                  }))
                }
                className="bg-background border border-border font-mono text-sm px-3 py-2 w-full"
              >
                {CATEGORY_OPTIONS.map((c) => (
                  <option key={c} value={c}>
                    {CATEGORY_LABELS[c]}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="tpl-subject">Asunto</Label>
            <Input
              id="tpl-subject"
              value={form.subject}
              onChange={(e) => setForm((p) => ({ ...p, subject: e.target.value }))}
              placeholder="ej: Aviso importante {{nombre}}"
              aria-label="Asunto"
            />
          </div>

          <div className="space-y-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <Label htmlFor="tpl-body">Cuerpo HTML</Label>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-muted-foreground">
                  Variables:
                </span>
                {TEMPLATE_VARIABLES.map((v) => (
                  <button
                    key={v}
                    type="button"
                    onClick={() => insertVariable(v)}
                    className="border border-border px-2 py-1 font-mono text-xs text-primary hover:bg-primary hover:text-background transition-colors"
                  >
                    {v}
                  </button>
                ))}
                <button
                  type="button"
                  onClick={() => setView(view === "source" ? "preview" : "source")}
                  className="inline-flex items-center gap-1 border border-border px-2 py-1 font-mono text-xs text-muted-foreground hover:text-primary transition-colors"
                >
                  {view === "source" ? (
                    <>
                      <Eye size={12} /> Vista previa
                    </>
                  ) : (
                    <>
                      <Code2 size={12} /> Fuente
                    </>
                  )}
                </button>
              </div>
            </div>

            {view === "source" ? (
              <Textarea
                id="tpl-body"
                ref={bodyRef}
                value={form.html_body}
                onChange={(e) => setForm((p) => ({ ...p, html_body: e.target.value }))}
                placeholder="<p>Hola {{nombre}}, su cuenta {{empresa}}…</p>"
                rows={10}
                className="font-mono text-sm"
                aria-label="Cuerpo HTML"
              />
            ) : (
              <div
                data-testid="preview"
                className="border border-border bg-background p-4 min-h-[10rem] overflow-auto"
                // The preview renders the tenant's own HTML with sample values
                // substituted for the variables — same trust model as the
                // backend renderer (spec R5).
                dangerouslySetInnerHTML={{ __html: renderPreview(form.html_body) }}
              />
            )}
          </div>

          <div className="flex gap-2">
            <Button type="submit" disabled={saving}>
              {saving ? <Loader2 size={16} className="animate-spin" /> : null}
              Guardar
            </Button>
            <Button type="button" variant="outline" onClick={closeEditor}>
              Cancelar
            </Button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="border border-border bg-card p-12 text-center">
          <Loader2 className="mx-auto text-primary mb-4 animate-spin" size={32} />
          <p className="font-mono text-sm text-muted-foreground">
            Cargando plantillas…
          </p>
        </div>
      ) : templates.length === 0 ? (
        <div className="border border-border bg-card p-12 text-center">
          <FileText className="mx-auto text-primary mb-4" size={32} />
          <p className="font-mono text-sm text-muted-foreground">
            Sin plantillas todavía. Creá la primera para empezar a simular.
          </p>
        </div>
      ) : (
        <div className="border border-border bg-card overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nombre</TableHead>
                <TableHead>Categoría</TableHead>
                <TableHead>Asunto</TableHead>
                <TableHead>Creada</TableHead>
                <TableHead>Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {templates.map((t) => (
                <TableRow key={t.id}>
                  <TableCell className="font-mono text-xs">{t.name}</TableCell>
                  <TableCell className="font-mono text-xs">{t.category}</TableCell>
                  <TableCell className="font-mono text-xs">{t.subject}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {new Date(t.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    <div className="flex flex-wrap gap-1">
                      <button
                        type="button"
                        aria-label={`Editar ${t.name}`}
                        onClick={() => openEdit(t)}
                        className="border border-border px-2 py-1 text-muted-foreground hover:text-primary"
                      >
                        <Pencil size={14} />
                      </button>
                      <button
                        type="button"
                        aria-label="Eliminar plantilla"
                        onClick={() => remove(t)}
                        className="border border-border px-2 py-1 text-muted-foreground hover:text-destructive"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
