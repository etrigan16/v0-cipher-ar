"use client"

import { useCallback, useEffect, useState } from "react"
import { api, type Asset, type Finding, type FindingStatus } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

export default function FindingsPage() {
  const [findings, setFindings] = useState<Finding[]>([])
  const [assets, setAssets] = useState<Asset[]>([])
  const [severity, setSeverity] = useState("")
  const [status, setStatus] = useState("")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)

  const assetName = useCallback(
    (assetId: string) => {
      const asset = assets.find((a) => a.id === assetId)
      return asset ? (asset.subdomain ?? asset.domain) : "—"
    },
    [assets]
  )

  const loadFindings = useCallback(
    async (severityFilter: string, statusFilter: string) => {
      try {
        const res = await api.asm.getFindings({
          severity: severityFilter || undefined,
          status: statusFilter || undefined,
        })
        setFindings(res.findings)
        setError(null)
      } catch (e) {
        setError(
          e instanceof Error ? e.message : "No se pudieron cargar los hallazgos"
        )
      } finally {
        setLoading(false)
      }
    },
    []
  )

  useEffect(() => {
    loadFindings("", "")
    api.asm
      .listAssets()
      .then((res) => setAssets(res.assets))
      .catch(() => {
        // Asset names fall back to the raw asset id when the list fails.
      })
  }, [loadFindings])

  const handleSeverityChange = (value: string) => {
    setSeverity(value)
    loadFindings(value, status)
  }

  const handleStatusChange = (value: string) => {
    setStatus(value)
    loadFindings(severity, value)
  }

  const changeStatus = async (id: string, next: FindingStatus) => {
    setBusyId(id)
    try {
      const updated = await api.asm.patchFinding(id, next)
      setFindings((prev) => prev.map((f) => (f.id === updated.id ? updated : f)))
      setError(null)
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "No se pudo actualizar el estado"
      )
    } finally {
      setBusyId(null)
    }
  }

  const enrich = async (id: string) => {
    setBusyId(id)
    try {
      const updated = await api.asm.enrichFinding(id)
      setFindings((prev) => prev.map((f) => (f.id === updated.id ? updated : f)))
      setError(null)
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "No se pudo enriquecer el hallazgo"
      )
    } finally {
      setBusyId(null)
    }
  }

  const download = async (format: "csv" | "pdf") => {
    try {
      const blob = await api.asm.exportFindings(format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = format === "csv" ? "asm-findings.csv" : "asm-findings.pdf"
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "No se pudo exportar el reporte"
      )
    }
  }

  const rowActionsDisabled = (f: Finding) => busyId === f.id

  return (
    <div>
      <div className="mb-8">
        <h1 className="font-mono text-2xl font-bold">
          FINDINGS<span className="text-primary">_</span>
        </h1>
        <p className="font-mono text-sm text-muted-foreground mt-1">
          Hallazgos de riesgo de tu superficie de ataque
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-4 mb-6">
        <div className="bg-card border border-border p-4">
          <label
            htmlFor="severity-filter"
            className="block font-mono text-xs text-muted-foreground mb-2"
          >
            SEVERIDAD
          </label>
          <select
            id="severity-filter"
            aria-label="Filtrar por severidad"
            value={severity}
            onChange={(e) => handleSeverityChange(e.target.value)}
            className="bg-background border border-border font-mono text-sm px-3 py-2"
          >
            <option value="">Todas</option>
            <option value="critical">Crítica</option>
            <option value="high">Alta</option>
            <option value="medium">Media</option>
            <option value="low">Baja</option>
            <option value="info">Info</option>
          </select>
        </div>

        <div className="bg-card border border-border p-4">
          <label
            htmlFor="status-filter"
            className="block font-mono text-xs text-muted-foreground mb-2"
          >
            ESTADO
          </label>
          <select
            id="status-filter"
            aria-label="Filtrar por estado"
            value={status}
            onChange={(e) => handleStatusChange(e.target.value)}
            className="bg-background border border-border font-mono text-sm px-3 py-2"
          >
            <option value="">Todos</option>
            <option value="open">Abiertos</option>
            <option value="resolved">Resueltos</option>
            <option value="fp">Falsos positivos</option>
          </select>
        </div>

        <div className="ml-auto flex gap-2">
          <Button variant="outline" size="sm" onClick={() => download("csv")}>
            Exportar CSV
          </Button>
          <Button variant="outline" size="sm" onClick={() => download("pdf")}>
            Exportar PDF
          </Button>
        </div>
      </div>

      {error && (
        <div role="alert" className="border border-destructive bg-card p-4 mb-6">
          <p className="font-mono text-sm text-destructive">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="border border-border bg-card p-12 text-center">
          <p className="font-mono text-sm text-muted-foreground">
            Cargando hallazgos…
          </p>
        </div>
      ) : findings.length === 0 ? (
        <div className="border border-border bg-card p-12 text-center">
          <p className="font-mono text-sm text-muted-foreground">
            Sin hallazgos todavía. Escaneá un dominio para generar hallazgos de
            riesgo.
          </p>
        </div>
      ) : (
        <div className="border border-border bg-card overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Severidad</TableHead>
                <TableHead>Riesgo</TableHead>
                <TableHead>Título</TableHead>
                <TableHead>Activo</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Enriquecido</TableHead>
                <TableHead>Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {findings.map((f) => (
                <TableRow key={f.id}>
                  <TableCell className="font-mono text-xs">{f.severity}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {f.risk_score ?? "—"}
                  </TableCell>
                  <TableCell className="font-mono text-xs">{f.title}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {assetName(f.asset_id)}
                  </TableCell>
                  <TableCell className="font-mono text-xs">{f.status}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {f.enriched_at
                      ? new Date(f.enriched_at).toLocaleDateString()
                      : "—"}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    <div className="flex flex-wrap gap-1">
                      <button
                        type="button"
                        aria-label="Reabrir hallazgo"
                        disabled={f.status === "open" || rowActionsDisabled(f)}
                        onClick={() => changeStatus(f.id, "open")}
                        className="border border-border px-2 py-1 text-muted-foreground hover:text-primary disabled:opacity-40"
                      >
                        Reabrir
                      </button>
                      <button
                        type="button"
                        aria-label="Resolver hallazgo"
                        disabled={f.status === "resolved" || rowActionsDisabled(f)}
                        onClick={() => changeStatus(f.id, "resolved")}
                        className="border border-border px-2 py-1 text-muted-foreground hover:text-primary disabled:opacity-40"
                      >
                        Resolver
                      </button>
                      <button
                        type="button"
                        aria-label="Marcar como falso positivo"
                        disabled={f.status === "fp" || rowActionsDisabled(f)}
                        onClick={() => changeStatus(f.id, "fp")}
                        className="border border-border px-2 py-1 text-muted-foreground hover:text-primary disabled:opacity-40"
                      >
                        FP
                      </button>
                      <button
                        type="button"
                        aria-label="Enriquecer hallazgo"
                        disabled={f.enriched_at != null || rowActionsDisabled(f)}
                        onClick={() => enrich(f.id)}
                        className="border border-border px-2 py-1 text-muted-foreground hover:text-primary disabled:opacity-40"
                      >
                        Enriquecer
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
