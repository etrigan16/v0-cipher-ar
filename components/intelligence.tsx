import { AlertTriangle, FileText, Shield, Clock } from "lucide-react"

const reports = [
  {
    type: "ALERTA",
    date: "2024-01-15",
    title: "CVE-2024-0001: Vulnerabilidad crítica en OpenSSL",
    severity: "CRÍTICO",
    excerpt: "Nueva vulnerabilidad de ejecución remota de código descubierta. Actualización inmediata recomendada.",
    icon: AlertTriangle,
  },
  {
    type: "ANÁLISIS",
    date: "2024-01-12",
    title: "Ransomware LockBit 3.0: Tácticas y mitigación",
    severity: "ALTO",
    excerpt: "Análisis técnico de las nuevas variantes y estrategias de defensa para infraestructuras PyME.",
    icon: FileText,
  },
  {
    type: "CASO",
    date: "2024-01-08",
    title: "De la brecha al blindaje: Caso empresa logística",
    severity: "RESUELTO",
    excerpt: "Cómo convertimos un incidente de seguridad en una oportunidad para fortalecer la infraestructura.",
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
