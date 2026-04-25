"use client"

import { useState } from "react"
import { Shield, Lock, Server, Eye, ChevronRight, Check } from "lucide-react"
import { Button } from "@/components/ui/button"

const palettes = [
  {
    id: "deep-blue",
    name: "Azul Profundo + Cyan",
    description: "Estilo dashboard de seguridad - Profesional y tecnológico",
    bg: "bg-[#0a0f1c]",
    cardBg: "bg-[#111827]",
    primary: "bg-[#1e40af]",
    accent: "text-[#06b6d4]",
    accentBg: "bg-[#06b6d4]",
    border: "border-[#1e3a5f]",
    text: "text-white",
    textMuted: "text-slate-400",
    buttonHover: "hover:bg-[#1e40af]/80",
  },
  {
    id: "matrix-green",
    name: "Verde Matriz + Negro",
    description: "Estilo terminal/hacker ético - Técnico y especializado",
    bg: "bg-[#0d0d0d]",
    cardBg: "bg-[#1a1a1a]",
    primary: "bg-[#10b981]",
    accent: "text-[#10b981]",
    accentBg: "bg-[#10b981]",
    border: "border-[#374151]",
    text: "text-white",
    textMuted: "text-gray-500",
    buttonHover: "hover:bg-[#10b981]/80",
  },
  {
    id: "slate-corp",
    name: "Slate Corporativo",
    description: "Más corporativo y sobrio - Confianza empresarial",
    bg: "bg-[#0f172a]",
    cardBg: "bg-[#1e293b]",
    primary: "bg-[#3b82f6]",
    accent: "text-[#3b82f6]",
    accentBg: "bg-[#3b82f6]",
    border: "border-[#334155]",
    text: "text-white",
    textMuted: "text-slate-400",
    buttonHover: "hover:bg-[#3b82f6]/80",
  },
]

function HeroMockup({ palette }: { palette: typeof palettes[0] }) {
  return (
    <div className={`${palette.bg} rounded-lg overflow-hidden`}>
      {/* Navbar */}
      <nav className={`flex items-center justify-between px-6 py-4 ${palette.border} border-b`}>
        <div className="flex items-center gap-2">
          <Shield className={`w-6 h-6 ${palette.accent}`} />
          <span className={`font-semibold ${palette.text}`}>Guillermo A. Fernandez</span>
        </div>
        <div className={`hidden md:flex items-center gap-6 text-sm ${palette.textMuted}`}>
          <span className="hover:text-white cursor-pointer">Servicios</span>
          <span className="hover:text-white cursor-pointer">Casos</span>
          <span className="hover:text-white cursor-pointer">Blog</span>
          <span className="hover:text-white cursor-pointer">Contacto</span>
        </div>
        <Button size="sm" className={`${palette.primary} text-white ${palette.buttonHover}`}>
          Consulta Gratis
        </Button>
      </nav>

      {/* Hero */}
      <div className="px-6 py-12 md:py-16">
        <div className="max-w-2xl">
          <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full ${palette.cardBg} ${palette.border} border text-sm ${palette.textMuted} mb-6`}>
            <Lock className={`w-3 h-3 ${palette.accent}`} />
            <span>Protección empresarial de nivel avanzado</span>
          </div>
          
          <h1 className={`text-3xl md:text-4xl font-bold ${palette.text} mb-4 leading-tight`}>
            Ciberseguridad para{" "}
            <span className={palette.accent}>PyMEs</span>{" "}
            que no pueden permitirse vulnerabilidades
          </h1>
          
          <p className={`${palette.textMuted} mb-8 text-base leading-relaxed`}>
            Auditorías de seguridad, análisis de infraestructura y protección de datos. 
            Soluciones adaptadas a tu presupuesto y necesidades específicas.
          </p>
          
          <div className="flex flex-wrap gap-3">
            <Button className={`${palette.primary} text-white ${palette.buttonHover}`}>
              Solicitar Auditoría
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
            <Button variant="outline" className={`${palette.border} border ${palette.text} bg-transparent hover:bg-white/10`}>
              Ver Casos de Estudio
            </Button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className={`grid grid-cols-3 gap-4 px-6 pb-8`}>
        {[
          { icon: Shield, label: "Empresas protegidas", value: "150+" },
          { icon: Server, label: "Auditorías realizadas", value: "300+" },
          { icon: Eye, label: "Vulnerabilidades detectadas", value: "2,500+" },
        ].map((stat, i) => (
          <div key={i} className={`${palette.cardBg} ${palette.border} border rounded-lg p-4`}>
            <stat.icon className={`w-5 h-5 ${palette.accent} mb-2`} />
            <div className={`text-xl font-bold ${palette.text}`}>{stat.value}</div>
            <div className={`text-xs ${palette.textMuted}`}>{stat.label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function PaletteSelector() {
  const [selected, setSelected] = useState<string | null>(null)

  return (
    <div className="min-h-screen bg-neutral-950 text-white p-6 md:p-10">
      <div className="max-w-6xl mx-auto">
        <header className="text-center mb-12">
          <h1 className="text-3xl md:text-4xl font-bold mb-4">
            Elige tu Paleta de Colores
          </h1>
          <p className="text-neutral-400 max-w-2xl mx-auto">
            Cada opción está diseñada para transmitir profesionalismo y confianza en el sector de ciberseguridad. 
            Haz clic en la que prefieras para seleccionarla.
          </p>
        </header>

        <div className="space-y-12">
          {palettes.map((palette) => (
            <div key={palette.id} className="space-y-4">
              <button
                onClick={() => setSelected(palette.id)}
                className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                  selected === palette.id
                    ? "border-cyan-500 bg-cyan-500/10"
                    : "border-neutral-700 hover:border-neutral-500"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                      {palette.name}
                      {selected === palette.id && (
                        <span className="inline-flex items-center gap-1 text-sm text-cyan-400">
                          <Check className="w-4 h-4" /> Seleccionada
                        </span>
                      )}
                    </h2>
                    <p className="text-neutral-400 text-sm">{palette.description}</p>
                  </div>
                  <div className="flex gap-2">
                    <div className={`w-8 h-8 rounded-full ${palette.bg} border border-neutral-600`} />
                    <div className={`w-8 h-8 rounded-full ${palette.primary}`} />
                    <div className={`w-8 h-8 rounded-full ${palette.accentBg}`} />
                  </div>
                </div>
              </button>
              
              <HeroMockup palette={palette} />
            </div>
          ))}
        </div>

        {selected && (
          <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-neutral-800 border border-neutral-700 rounded-full px-6 py-3 shadow-xl flex items-center gap-4">
            <span className="text-sm">
              Seleccionaste: <strong>{palettes.find(p => p.id === selected)?.name}</strong>
            </span>
            <span className="text-neutral-500 text-sm">
              Dime cuál te gusta y continuamos
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
