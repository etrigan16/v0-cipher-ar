import { Crosshair, Eye, Activity, AlertTriangle } from "lucide-react"

const features = [
  {
    icon: Crosshair,
    title: "ASSET DISCOVERY",
    desc: "Descubrimiento automático de activos expuestos: subdominios, IPs, certificados, y servicios olvidados.",
  },
  {
    icon: Eye,
    title: "CONTINUOUS MONITORING",
    desc: "Escaneo periódico de tu superficie de ataque. Detectamos cambios y nuevas exposiciones en tiempo real.",
  },
  {
    icon: Activity,
    title: "RISK SCORING",
    desc: "Priorización de vulnerabilidades por criticidad, explotabilidad y contexto de tu infraestructura.",
  },
  {
    icon: AlertTriangle,
    title: "ALERTAS PROACTIVAS",
    desc: "Notificaciones instantáneas ante nuevos riesgos. Slack, email o webhook. Tú eliges.",
  },
]

export function AttackSurfaceSection() {
  return (
    <section id="asm" className="px-4 sm:px-6 lg:px-8 py-20 bg-surface-2">
      <div className="max-w-7xl mx-auto">
        <div className="max-w-2xl mb-16">
          <span className="font-mono text-xs text-primary tracking-[0.2em]">PRODUCTO</span>
          <h2 className="font-mono text-3xl sm:text-4xl font-bold mt-4 mb-4">
            ATTACK SURFACE<span className="text-primary">_</span>
            <br />
            <span className="text-muted-foreground">MANAGEMENT</span>
          </h2>
          <p className="text-muted-foreground font-mono text-sm leading-relaxed">
            Monitoreo continuo de tu superficie de ataque externa. Detectamos activos
            olvidados, puertos abiertos, y vulnerabilidades antes de que lo hagan los
            atacantes.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-px bg-border">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="bg-surface-1 p-8 hover:bg-surface-3 transition-colors"
            >
              <feature.icon className="text-primary mb-6" size={28} />
              <h3 className="font-mono text-sm text-primary mb-3 tracking-wider">
                {feature.title}
              </h3>
              <p className="font-mono text-sm text-muted-foreground leading-relaxed">
                {feature.desc}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <a
            href="/register"
            className="inline-flex items-center gap-2 font-mono text-sm border border-primary px-6 py-3 text-primary hover:bg-primary hover:text-background transition-colors"
          >
            Comenzar prueba gratuita
          </a>
        </div>
      </div>
    </section>
  )
}
