"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { Download, Loader2, MousePointerClick, ShieldAlert } from "lucide-react"
import { api, type TargetResult } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

/** Per-campaign aggregate cards (spec R4): counts + engagement rates. */
function summarizeTargets(targets: TargetResult[]) {
  const sent = targets.filter((t) => t.status === "active").length
  const opened = targets.filter((t) => t.opened).length
  const clicked = targets.filter((t) => t.clicked).length
  const credentials = targets.filter((t) => t.credential).length
  const rate = (count: number) => (sent ? Math.round((count / sent) * 100) : 0)
  return {
    total: targets.length,
    sent,
    opened,
    opened_rate: rate(opened),
    clicked,
    clicked_rate: rate(clicked),
    credentials,
  }
}

export default function ResultsDetailPage() {
  const params = useParams<{ id: string }>()
  const campaignId = params.id

  const [targets, setTargets] = useState<TargetResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    api.phishing
      .getCampaignResults(campaignId)
      .then((res) => {
        if (active) {
          setTargets(res.targets)
          setError(null)
        }
      })
      .catch((e) => {
        if (active) {
          setError(e instanceof Error ? e.message : "No se pudieron cargar los resultados")
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [campaignId])

  const download = async (format: "csv" | "pdf") => {
    try {
      const blob = await api.phishing.exportCampaign(campaignId, format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download =
        format === "csv" ? `phishing-results-${campaignId}.csv` : `phishing-results-${campaignId}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo exportar el reporte")
    }
  }

  const summary = summarizeTargets(targets)

  const cards = [
    { label: "SENT", value: String(summary.sent), icon: MousePointerClick },
    {
      label: "ABIERTOS",
      value: `${summary.opened} (${summary.opened_rate}%)`,
      icon: MousePointerClick,
    },
    {
      label: "CLICKS",
      value: `${summary.clicked} (${summary.clicked_rate}%)`,
      icon: MousePointerClick,
    },
    { label: "CREDENCIALES", value: String(summary.credentials), icon: ShieldAlert },
  ]

  return (
    <div>
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-mono text-2xl font-bold">
            RESULTADOS DE CAMPAÑA<span className="text-primary">_</span>
          </h1>
          <p className="font-mono text-sm text-muted-foreground mt-1">
            Detalle por target y exportación del reporte
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => download("csv")}>
            <Download size={14} />
            Exportar CSV
          </Button>
          <Button variant="outline" size="sm" onClick={() => download("pdf")}>
            <Download size={14} />
            Exportar PDF
          </Button>
        </div>
      </div>

      {error && (
        <div role="alert" className="border border-destructive bg-card p-4 mb-6">
          <p className="font-mono text-sm text-destructive">{error}</p>
        </div>
      )}

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-px bg-border mb-8">
        {cards.map((card) => (
          <div key={card.label} className="bg-card p-6">
            <card.icon className="text-primary mb-4" size={24} />
            <div className="font-mono text-3xl font-bold mb-1">{card.value}</div>
            <div className="font-mono text-xs text-muted-foreground">
              {card.label}
            </div>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="border border-border bg-card p-12 text-center">
          <Loader2 className="mx-auto text-primary mb-4 animate-spin" size={32} />
          <p className="font-mono text-sm text-muted-foreground">
            Cargando resultados…
          </p>
        </div>
      ) : targets.length === 0 ? (
        <div className="border border-border bg-card p-12 text-center">
          <ShieldAlert className="mx-auto text-primary mb-4" size={32} />
          <p className="font-mono text-sm text-muted-foreground">
            Sin resultados todavía. Esta campaña no registró actividad.
          </p>
        </div>
      ) : (
        <div className="border border-border bg-card overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Email</TableHead>
                <TableHead>Nombre</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Abierto</TableHead>
                <TableHead>Click</TableHead>
                <TableHead>Credencial</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {targets.map((t) => (
                <TableRow key={t.email}>
                  <TableCell className="font-mono text-xs">{t.email}</TableCell>
                  <TableCell className="font-mono text-xs">{t.name}</TableCell>
                  <TableCell className="font-mono text-xs">{t.status}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {t.opened ? "true" : "false"}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {t.clicked ? "true" : "false"}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {t.credential ? "true" : "false"}
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
