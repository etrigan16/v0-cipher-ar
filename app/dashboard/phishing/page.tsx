"use client"

import { Siren, Plus, Users } from "lucide-react"

export default function PhishingPage() {
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

      <div className="grid md:grid-cols-2 gap-px bg-border mb-8">
        <div className="bg-card p-6">
          <span className="font-mono text-xs text-muted-foreground">Campañas activas</span>
          <div className="font-mono text-4xl font-bold mt-2">0</div>
        </div>
        <div className="bg-card p-6">
          <span className="font-mono text-xs text-muted-foreground">USUARIOS ENTRENADOS</span>
          <div className="font-mono text-4xl font-bold mt-2">0</div>
        </div>
      </div>

      <div className="border border-border bg-card p-12 text-center">
        <Siren className="mx-auto text-primary mb-4" size={32} />
        <p className="font-mono text-sm text-muted-foreground mb-6">
          Creá tu primera campaña de phishing para medir la resiliencia de tu equipo.
        </p>
        <button
          disabled
          className="inline-flex items-center gap-2 font-mono text-sm border border-primary px-6 py-3 text-primary hover:bg-primary hover:text-background transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Plus size={16} />
          Nueva campaña
        </button>
      </div>
    </div>
  )
}
