"use client"

import Link from "next/link"
import { BarChart3, FileText, Send, Siren } from "lucide-react"

const sections = [
  {
    href: "/dashboard/phishing/templates",
    title: "Plantillas",
    description:
      "Creá y editá plantillas de phishing con variables por destinatario.",
    icon: FileText,
  },
  {
    href: "/dashboard/phishing/campaigns",
    title: "Campañas",
    description:
      "Creá campañas, subí targets en CSV, lanzalas y cancelalas.",
    icon: Send,
  },
  {
    href: "/dashboard/phishing/results",
    title: "Resultados",
    description:
      "Métricas agregadas, detalle por target y exportación de reportes.",
    icon: BarChart3,
  },
]

export default function PhishingHubPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="font-mono text-2xl font-bold">
          PHISHING SIMULATION<span className="text-primary">_</span>
        </h1>
        <p className="font-mono text-sm text-muted-foreground mt-1">
          Simulaciones y entrenamiento
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-px bg-border">
        {sections.map((section) => (
          <Link
            key={section.href}
            href={section.href}
            className="bg-card p-6 hover:bg-surface-3 transition-colors"
          >
            <section.icon className="text-primary mb-4" size={24} />
            <h2 className="font-mono text-sm font-bold mb-1">{section.title}</h2>
            <p className="font-mono text-xs text-muted-foreground">
              {section.description}
            </p>
          </Link>
        ))}
      </div>

      <div className="mt-8 border border-border bg-card p-12 text-center">
        <Siren className="mx-auto text-primary mb-4" size={32} />
        <p className="font-mono text-sm text-muted-foreground mb-6">
          Empezá por crear una plantilla y luego lanzá tu primera campaña de
          phishing para medir la resiliencia de tu equipo.
        </p>
        <Link
          href="/dashboard/phishing/campaigns"
          className="inline-flex items-center gap-2 font-mono text-sm border border-primary px-6 py-3 text-primary hover:bg-primary hover:text-background transition-colors"
        >
          <Send size={16} />
          Ir a campañas
        </Link>
      </div>
    </div>
  )
}
