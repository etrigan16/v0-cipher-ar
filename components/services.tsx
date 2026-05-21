import { Network, Code, Users } from "lucide-react"

const pillars = [
  {
    icon: Network,
    number: "01",
    title: "NETWORKING & SECURITY",
    subtitle: "Arquitectura de red blindada",
    features: [
      { label: "SEGMENTACIÓN VLAN", desc: "Diseño e implementación de VLANs para aislamiento de tráfico crítico y contención de amenazas laterales." },
      { label: "FIREWALLS CLI", desc: "Configuración avanzada de Firewalls via línea de comandos (pfSense, iptables, Cisco IOS) para máximo control." },
      { label: "ZERO TRUST", desc: "Políticas de acceso basadas en identidad y contexto. Nada se confía por defecto." },
    ],
  },
  {
    icon: Code,
    number: "02",
    title: "SECURE SOFTWARE",
    subtitle: "Desarrollo con seguridad nativa",
    features: [
      { label: "BACKEND NEST.JS", desc: "APIs robustas con NestJS, validación estricta, guards de autenticación y PostgreSQL hardened." },
      { label: "FRONTEND NEXT.JS", desc: "Interfaces con Next.js App Router, Server Components y protección contra XSS/CSRF incorporada." },
      { label: "SESIONES HTTPONLY", desc: "Autenticación blindada con HttpOnly Cookies, refresh tokens seguros y rotación automática." },
    ],
  },
  {
    icon: Users,
    number: "03",
    title: "ARCHITECTURE & PM",
    subtitle: "Liderazgo técnico estratégico",
    features: [
      { label: "TURBOREPO", desc: "Arquitectura de Monorepos con Turborepo para startups que necesitan escalar sin deuda técnica." },
      { label: "SCRUM PARA MVPS", desc: "Metodología ágil adaptada: sprints cortos, demos frecuentes y entrega continua de valor." },
      { label: "TECH DUE DILIGENCE", desc: "Auditoría de arquitectura existente para inversores, adquisiciones o refactoring estratégico." },
    ],
  },
]

export function ServicesSection() {
  return (
    <section id="soluciones" className="px-4 sm:px-6 lg:px-8 py-20 bg-background border-b border-border">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-16">
          <p className="font-mono text-sm text-primary mb-2">// SOLUCIONES</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
            Tres pilares de protección
          </h2>
          <p className="text-muted-foreground max-w-2xl">
            Servicios diseñados para empresas que necesitan infraestructura robusta, software blindado y liderazgo técnico sin compromisos.
          </p>
        </div>

        {/* Pillars Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-px bg-border">
          {pillars.map((pillar) => {
            const Icon = pillar.icon
            return (
              <div
                key={pillar.number}
                className="bg-background p-8 border border-border hover:border-primary transition-colors group"
              >
                {/* Pillar Header */}
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <span className="font-mono text-xs text-muted-foreground">PILAR {pillar.number}</span>
                    <h3 className="font-mono text-lg font-bold text-foreground mt-1 group-hover:text-primary transition-colors">
                      {pillar.title}
                    </h3>
                    <p className="text-sm text-muted-foreground mt-1">{pillar.subtitle}</p>
                  </div>
                  <Icon className="w-8 h-8 text-primary/50 group-hover:text-primary transition-colors" />
                </div>

                {/* Features */}
                <div className="space-y-4 border-t border-border pt-6">
                  {pillar.features.map((feature, i) => (
                    <div key={i}>
                      <span className="font-mono text-xs text-primary">{feature.label}</span>
                      <p className="text-sm text-muted-foreground mt-1">{feature.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
