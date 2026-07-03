"use client"

import { useAuth } from "@/components/auth-context"
import { Crosshair, Siren, Activity, AlertTriangle } from "lucide-react"

const stats = [
  { label: "Activos monitoreados", value: "0", icon: Crosshair, color: "text-primary" },
  { label: "Vulnerabilidades activas", value: "0", icon: AlertTriangle, color: "text-destructive" },
  { label: "Campañas de phishing", value: "0", icon: Siren, color: "text-chart-3" },
  { label: "Escaneos este mes", value: "0", icon: Activity, color: "text-chart-5" },
]

export default function DashboardPage() {
  const { user } = useAuth()

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
        {stats.map((stat) => (
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
          href="/register"
          className="inline-flex items-center gap-2 font-mono text-sm border border-primary px-6 py-3 text-primary hover:bg-primary hover:text-background transition-colors"
        >
          Configurar monitoreo
        </a>
      </div>
    </div>
  )
}
