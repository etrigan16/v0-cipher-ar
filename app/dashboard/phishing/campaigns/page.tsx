"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import Link from "next/link"
import {
  BarChart3,
  Loader2,
  Plus,
  Rocket,
  Send,
  Upload,
  XCircle,
} from "lucide-react"
import { api, type Campaign, type LaunchedTarget, type Target, type Template } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

const STATUS_LABELS: Record<string, string> = {
  draft: "Borrador",
  active: "Activa",
  completed: "Completada",
  cancelled: "Cancelada",
}

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Create form state.
  const [creating, setCreating] = useState(false)
  const [name, setName] = useState("")
  const [templateId, setTemplateId] = useState("")
  const [creatingBusy, setCreatingBusy] = useState(false)

  // Detail state: the selected campaign, its targets, CSV upload + actions.
  const [selected, setSelected] = useState<Campaign | null>(null)
  const [targets, setTargets] = useState<Target[]>([])
  const [detailLoading, setDetailLoading] = useState(false)
  const [launched, setLaunched] = useState<LaunchedTarget[] | null>(null)
  const [uploadMsg, setUploadMsg] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const refreshCampaigns = useCallback(async () => {
    const [campaignsRes, templatesRes] = await Promise.all([
      api.phishing.listCampaigns(),
      api.phishing.listTemplates(),
    ])
    setCampaigns(campaignsRes.campaigns)
    setTemplates(templatesRes.templates)
  }, [])

  const loadDetail = useCallback(async (campaign: Campaign) => {
    setSelected(campaign)
    setDetailLoading(true)
    setLaunched(null)
    setUploadMsg(null)
    try {
      const res = await api.phishing.listTargets(campaign.id)
      setTargets(res.targets)
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron cargar los targets")
    } finally {
      setDetailLoading(false)
    }
  }, [])

  useEffect(() => {
    let active = true
    refreshCampaigns()
      .then(() => {
        if (active) setError(null)
      })
      .catch((e) => {
        if (active) {
          setError(e instanceof Error ? e.message : "No se pudieron cargar las campañas")
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [refreshCampaigns])

  const createCampaign = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !templateId) {
      setError("Nombre y plantilla son obligatorios")
      return
    }
    setCreatingBusy(true)
    setError(null)
    try {
      const created = await api.phishing.createCampaign({
        name: name.trim(),
        template_id: templateId,
      })
      await refreshCampaigns()
      setCreating(false)
      setName("")
      setTemplateId("")
      setSelected(created)
      await loadDetail(created)
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear la campaña")
    } finally {
      setCreatingBusy(false)
    }
  }

  const uploadTargets = async () => {
    const file = fileRef.current?.files?.[0]
    if (!file || !selected) return
    setBusy(true)
    setError(null)
    try {
      const res = await api.phishing.uploadTargets(selected.id, file)
      setTargets(res.targets)
      setUploadMsg(`${res.count} targets subidos`)
      await refreshCampaigns()
      const updated = campaigns.find((c) => c.id === selected.id)
      if (updated) setSelected(updated)
      if (fileRef.current) fileRef.current.value = ""
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo subir el CSV")
    } finally {
      setBusy(false)
    }
  }

  const launch = async () => {
    if (!selected) return
    setBusy(true)
    setError(null)
    try {
      const res = await api.phishing.launchCampaign(selected.id)
      setLaunched(res.targets)
      setSelected(res.campaign)
      await refreshCampaigns()
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo lanzar la campaña")
    } finally {
      setBusy(false)
    }
  }

  const cancel = async () => {
    if (!selected) return
    setBusy(true)
    setError(null)
    try {
      const updated = await api.phishing.cancelCampaign(selected.id)
      setSelected(updated)
      await refreshCampaigns()
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cancelar la campaña")
    } finally {
      setBusy(false)
    }
  }

  const templateName = (id: string) =>
    templates.find((t) => t.id === id)?.name ?? "—"

  return (
    <div>
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-mono text-2xl font-bold">
            CAMPAÑAS<span className="text-primary">_</span>
          </h1>
          <p className="font-mono text-sm text-muted-foreground mt-1">
            Simulaciones de phishing por campaña
          </p>
        </div>
        {!creating && (
          <Button onClick={() => setCreating(true)}>
            <Plus size={16} />
            Nueva campaña
          </Button>
        )}
      </div>

      {error && (
        <div role="alert" className="border border-destructive bg-card p-4 mb-6">
          <p className="font-mono text-sm text-destructive">{error}</p>
        </div>
      )}

      {creating && (
        <form
          onSubmit={createCampaign}
          className="border border-border bg-card p-6 mb-8 space-y-4"
        >
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="camp-name">Nombre de la campaña</Label>
              <Input
                id="camp-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="ej: Campaña Q1"
                aria-label="Nombre de la campaña"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="camp-template">Plantilla</Label>
              <select
                id="camp-template"
                aria-label="Plantilla"
                value={templateId}
                onChange={(e) => setTemplateId(e.target.value)}
                className="bg-background border border-border font-mono text-sm px-3 py-2 w-full"
              >
                <option value="">Seleccioná una plantilla</option>
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <Button type="submit" disabled={creatingBusy}>
              {creatingBusy ? <Loader2 size={16} className="animate-spin" /> : null}
              Crear campaña
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setCreating(false)}
            >
              Cancelar
            </Button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="border border-border bg-card p-12 text-center">
          <Loader2 className="mx-auto text-primary mb-4 animate-spin" size={32} />
          <p className="font-mono text-sm text-muted-foreground">
            Cargando campañas…
          </p>
        </div>
      ) : campaigns.length === 0 ? (
        <div className="border border-border bg-card p-12 text-center">
          <Send className="mx-auto text-primary mb-4" size={32} />
          <p className="font-mono text-sm text-muted-foreground">
            Sin campañas todavía. Creá la primera para empezar a simular.
          </p>
        </div>
      ) : (
        <div className="border border-border bg-card overflow-x-auto mb-8">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nombre</TableHead>
                <TableHead>Plantilla</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Targets</TableHead>
                <TableHead>Creada</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {campaigns.map((c) => (
                <TableRow
                  key={c.id}
                  onClick={() => loadDetail(c)}
                  className="cursor-pointer hover:bg-surface-3"
                >
                  <TableCell className="font-mono text-xs">{c.name}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {templateName(c.template_id)}
                  </TableCell>
                  <TableCell className="font-mono text-xs">{c.status}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {c.target_count}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {new Date(c.created_at).toLocaleDateString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {selected && (
        <div className="border border-border bg-card p-6">
          <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
            <div>
              <h2 className="font-mono text-lg font-bold">
                {selected.name}
                <span className="ml-2 font-mono text-xs text-primary">
                  {STATUS_LABELS[selected.status] ?? selected.status}
                </span>
              </h2>
              <p className="font-mono text-xs text-muted-foreground mt-1">
                Plantilla: {templateName(selected.template_id)}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {selected.status === "draft" && (
                <>
                  <input
                    ref={fileRef}
                    type="file"
                    accept=".csv,text/csv"
                    aria-label="Archivo CSV de targets"
                    className="hidden"
                    onChange={uploadTargets}
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={busy}
                    onClick={() => fileRef.current?.click()}
                  >
                    <Upload size={14} />
                    Subir CSV
                  </Button>
                  <Button size="sm" disabled={busy || targets.length === 0} onClick={launch}>
                    <Rocket size={14} />
                    Lanzar
                  </Button>
                </>
              )}
              {(selected.status === "draft" || selected.status === "active") && (
                <Button
                  variant="outline"
                  size="sm"
                  disabled={busy}
                  onClick={cancel}
                >
                  <XCircle size={14} />
                  Cancelar
                </Button>
              )}
              <Link
                href={`/dashboard/phishing/results/${selected.id}`}
                className="inline-flex items-center gap-2 font-mono text-xs border border-primary px-3 py-2 text-primary hover:bg-primary hover:text-background transition-colors"
              >
                <BarChart3 size={14} />
                Ver resultados
              </Link>
            </div>
          </div>

          {uploadMsg && (
            <p
              role="status"
              className="font-mono text-xs text-primary mb-4"
            >
              {uploadMsg}
            </p>
          )}

          {launched && launched.length > 0 && (
            <div className="border border-primary bg-background p-4 mb-6">
              <p className="font-mono text-sm text-primary mb-3">
                Campaña lanzada — {launched.length} links de distribución
                generados (envío manual, links-only):
              </p>
              <ul className="space-y-1">
                {launched.map((t) => (
                  <li key={t.id} className="font-mono text-xs text-muted-foreground">
                    <span className="text-foreground">{t.email}</span> →{" "}
                    <span className="break-all">{t.landing_url}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {detailLoading ? (
            <div className="border border-border bg-background p-8 text-center">
              <Loader2 className="mx-auto text-primary mb-3 animate-spin" size={24} />
              <p className="font-mono text-xs text-muted-foreground">
                Cargando targets…
              </p>
            </div>
          ) : targets.length === 0 ? (
            <div className="border border-border bg-background p-8 text-center">
              <p className="font-mono text-xs text-muted-foreground">
                Sin targets todavía. Subí un CSV con columnas{" "}
                <span className="text-primary">email,name</span>.
              </p>
            </div>
          ) : (
            <div className="border border-border bg-background overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Email</TableHead>
                    <TableHead>Nombre</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Token</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {targets.map((t) => (
                    <TableRow key={t.id}>
                      <TableCell className="font-mono text-xs">{t.email}</TableCell>
                      <TableCell className="font-mono text-xs">{t.name}</TableCell>
                      <TableCell className="font-mono text-xs">{t.status}</TableCell>
                      <TableCell className="font-mono text-xs">
                        {t.tracking_token ?? "—"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
