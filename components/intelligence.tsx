import { AlertTriangle, FileText, Shield, Clock } from "lucide-react"

const reports = [
  {
    type: "ANÁLISIS",
    date: "2024-01-15",
    title: "Robo de sesiones web: Por qué LocalStorage es el mejor amigo de un ataque XSS",
    severity: "CRÍTICO",
    excerpt: "Análisis técnico de cómo los tokens almacenados en LocalStorage quedan expuestos a scripts maliciosos. Alternativas seguras con HttpOnly Cookies.",
    icon: AlertTriangle,
  },
  {
    type: "INFRAESTRUCTURA",
    date: "2024-01-12",
    title: "Redes corporativas planas: El peligro oculto de no segmentar tu infraestructura",
    severity: "ALTO",
    excerpt: "Por qué una red sin VLANs permite que un atacante se mueva lateralmente. Guía de segmentación para PyMEs.",
    icon: FileText,
  },
  {
    type: "CASO",
    date: "2024-01-08",
    title: "Migración de arquitectura: Llevando un frontend de Vite a Next.js App Router",
    severity: "RESUELTO",
    excerpt: "Caso real de migración: problemas encontrados, decisiones de arquitectura y mejoras de rendimiento obtenidas.",
    icon: Shield,
  },
]

export function IntelligenceSection() {
  return (
    <section id="intelligence" className="px-4 sm:px-6 lg:px-8 py-20 bg-card border-b border-border">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <p className="font-mono text-sm text-primary mb-2">// CIPHER INTELLIGENCE</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
            Repositorio de inteligencia técnica
          </h2>
          <p className="text-muted-foreground max-w-2xl">
            No es un blog. Es información clasificada: análisis de vulnerabilidades, guías de mitigación y casos de estudio reales.
          </p>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-border">
          {reports.map((report, i) => {
            const Icon = report.icon
            return (
              <article
                key={i}
                className="bg-background p-6 border border-border hover:border-primary transition-colors group cursor-pointer"
              >
                {/* Meta */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <span className={`font-mono text-xs px-2 py-1 ${
                      report.severity === "CRÍTICO" 
                        ? "bg-destructive/20 text-destructive" 
                        : report.severity === "ALTO"
                        ? "bg-primary/20 text-primary"
                        : "bg-primary/10 text-primary"
                    }`}>
                      {report.severity}
                    </span>
                    <span className="font-mono text-xs text-muted-foreground">{report.type}</span>
                  </div>
                  <Icon className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
                </div>

                {/* Content */}
                <h3 className="font-mono text-sm font-bold text-foreground mb-2 group-hover:text-primary transition-colors leading-tight">
                  {report.title}
                </h3>
                <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                  {report.excerpt}
                </p>

                {/* Footer */}
                <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
                  <Clock className="w-3 h-3" />
                  {report.date}
                </div>
              </article>
            )
          })}
        </div>

        {/* CTA */}
        <div className="mt-8 text-center">
          <a
            href="#"
            className="inline-flex items-center gap-2 font-mono text-sm text-primary hover:underline"
          >
            Ver todos los reportes →
          </a>
        </div>
      </div>
    </section>
  )
}
