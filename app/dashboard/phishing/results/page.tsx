"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { BarChart3, Loader2, MousePointerClick, ShieldAlert } from "lucide-react"
import { api, type Campaign, type ResultsSummary } from "@/lib/api"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

const ZERO_SUMMARY: ResultsSummary = {
  total_targets: 0,
  sent: 0,
  opened_count: 0,
  opened_rate: 0,
  clicked_count: 0,
  clicked_rate: 0,
  credentials_count: 0,
  reported_count: 0,
}

export default function ResultsPage() {
  const [summary, setSummary] = useState<ResultsSummary>(ZERO_SUMMARY)
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    Promise.all([api.phishing.getResultsSummary(), api.phishing.listCampaigns()])
      .then(([summaryRes, campaignsRes]) => {
        if (active) {
          setSummary(summaryRes)
          setCampaigns(campaignsRes.campaigns)
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
  }, [])

  const cards = [
    {
      label: "TOTAL TARGETS",
      value: String(summary.total_targets),
      icon: BarChart3,
    },
    {
      label: "ABIERTOS",
      value: `${summary.opened_count} (${summary.opened_rate}%)`,
      icon: MousePointerClick,
    },
    {
      label: "CLICKS",
      value: `${summary.clicked_count} (${summary.clicked_rate}%)`,
      icon: MousePointerClick,
    },
    {
      label: "CREDENCIALES",
      value: String(summary.credentials_count),
      icon: ShieldAlert,
    },
  ]

  return (
    <div>
      <div className="mb-8">
        <h1 className="font-mono text-2xl font-bold">
          RESULTADOS<span className="text-primary">_</span>
        </h1>
        <p className="font-mono text-sm text-muted-foreground mt-1">
          Métricas agregadas de tus campañas de phishing
        </p>
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
      ) : campaigns.length === 0 ? (
        <div className="border border-border bg-card p-12 text-center">
          <BarChart3 className="mx-auto text-primary mb-4" size={32} />
          <p className="font-mono text-sm text-muted-foreground">
            Sin actividad todavía. Lanzá una campaña para ver resultados.
          </p>
        </div>
      ) : (
        <div className="border border-border bg-card overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Campaña</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Targets</TableHead>
                <TableHead>Creada</TableHead>
                <TableHead>Detalle</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {campaigns.map((c) => (
                <TableRow key={c.id}>
                  <TableCell className="font-mono text-xs">{c.name}</TableCell>
                  <TableCell className="font-mono text-xs">{c.status}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {c.target_count}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {new Date(c.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    <Link
                      href={`/dashboard/phishing/results/${c.id}`}
                      aria-label={`Ver resultados de ${c.name}`}
                      className="inline-flex items-center gap-2 font-mono text-xs border border-primary px-3 py-2 text-primary hover:bg-primary hover:text-background transition-colors"
                    >
                      <BarChart3 size={14} />
                      Ver resultados
                    </Link>
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
