"use client"

import { useEffect, useState } from "react"
import { useAuth } from "@/components/auth-context"
import { api } from "@/lib/api"
import { Crosshair, Siren, Activity, AlertTriangle } from "lucide-react"

type Stats = { assets: number; findings: number; scans: number }

const EMPTY_STATS: Stats = { assets: 0, findings: 0, scans: 0 }

export default function DashboardPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    api.asm
      .getStats()
      .then((res) => {
        if (active) setStats(res)
      })
      .catch(() => {
        // Keep the cards readable (zeros) instead of crashing the dashboard.
        if (active) setStats(EMPTY_STATS)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  const statCards = [
    { label: "Activos monitoreados", value: loading ? "…" : String(stats?.assets ?? 0), icon: Crosshair, color: "text-primary" },
    { label: "Vulnerabilidades activas", value: loading ? "…" : String(stats?.findings ?? 0), icon: AlertTriangle, color: "text-destructive" },
    { label: "Campañas de phishing", value: "0", icon: Siren, color: "text-chart-3" },
    { label: "Escaneos este mes", value: loading ? "…" : String(stats?.scans ?? 0), icon: Activity, color: "text-chart-5" },
  ]

  return (
    <div>
      <div className="mb-8">
        <h1 className="font-mono text-2xl font-bold">
          DASHBOARD<span className="text-primary">_</span>
        </h1>
        <p className="font-mono text-sm text-muted-foreground mt-1">
          Bienvenido, {user?.name || "Usuario"}
        </p>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-px bg-border">
        {statCards.map((stat) => (
          <div key={stat.label} className="bg-card p-6">
            <stat.icon className={`${stat.color} mb-4`} size={24} />
            <div className="font-mono text-3xl font-bold mb-1">{stat.value}</div>
            <div className="font-mono text-xs text-muted-foreground">{stat.label}</div>
          </div>
        ))}
      </div>

      <div className="mt-8 border border-border bg-card p-8 text-center">
        <p className="font-mono text-sm text-muted-foreground mb-4">
          Conectá el backend para ver datos reales de tu infraestructura.
        </p>
        <a
          href="/dashboard/attack-surface"
          className="inline-flex items-center gap-2 font-mono text-sm border border-primary px-6 py-3 text-primary hover:bg-primary hover:text-background transition-colors"
        >
          Configurar monitoreo
        </a>
      </div>
    </div>
  )
}
