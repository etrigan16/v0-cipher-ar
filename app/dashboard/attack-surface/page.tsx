"use client"

import { Crosshair, Plus, Search } from "lucide-react"

export default function AttackSurfacePage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="font-mono text-2xl font-bold">
          ATTACK SURFACE<span className="text-primary">_</span>
        </h1>
        <p className="font-mono text-sm text-muted-foreground mt-1">
          Monitoreo de superficie de ataque
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-px bg-border mb-8">
        <div className="bg-card p-6">
          <label className="block font-mono text-xs text-muted-foreground mb-2">
            DOMINIO / IP
          </label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                placeholder="ej: empresa.com"
                className="w-full bg-background border border-border pl-10 pr-4 py-3 font-mono text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none transition-colors"
              />
            </div>
            <button className="flex items-center gap-2 font-mono text-sm bg-primary text-background px-4 py-3 hover:bg-primary/90 transition-colors">
              <Plus size={16} />
              Agregar
            </button>
          </div>
        </div>

        <div className="bg-card p-6">
          <span className="font-mono text-xs text-muted-foreground">ACTIVOS MONITOREADOS</span>
          <div className="font-mono text-4xl font-bold mt-2">0</div>
        </div>
      </div>

      <div className="border border-border bg-card p-12 text-center">
        <Crosshair className="mx-auto text-primary mb-4" size={32} />
        <p className="font-mono text-sm text-muted-foreground">
          Agregá un dominio o IP para comenzar el monitoreo.
        </p>
      </div>
    </div>
  )
}
