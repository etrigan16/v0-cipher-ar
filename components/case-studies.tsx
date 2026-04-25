import { ArrowRight, Wifi, Server, Shield, Lock } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"

const caseStudies = [
  {
    icon: Wifi,
    category: "Seguridad de Red",
    title: "Segmentacion de Red WiFi Empresarial",
    description: "Implementacion de redes separadas para empleados e invitados, con diferenciacion de recursos y politicas de acceso.",
    results: ["Aislamiento completo de trafico", "Control de ancho de banda", "Acceso seguro a recursos internos"],
    tags: ["WiFi", "Segmentacion", "VLAN"]
  },
  {
    icon: Server,
    category: "Infraestructura",
    title: "Hardening de Servidores Windows/Linux",
    description: "Proceso de fortalecimiento de servidores criticos, eliminando vulnerabilidades y configurando politicas de seguridad.",
    results: ["Reduccion del 85% de superficie de ataque", "Cumplimiento de estandares CIS", "Monitoreo continuo"],
    tags: ["Hardening", "Servidores", "CIS"]
  },
  {
    icon: Shield,
    category: "Auditoria",
    title: "Analisis de Vulnerabilidades en PyME",
    description: "Evaluacion completa de seguridad para una empresa de 50 empleados, identificando riesgos criticos.",
    results: ["12 vulnerabilidades criticas detectadas", "Plan de remediacion priorizado", "Capacitacion del personal"],
    tags: ["Auditoria", "Vulnerabilidades", "PyME"]
  },
  {
    icon: Lock,
    category: "Proteccion de Datos",
    title: "Implementacion de Cifrado End-to-End",
    description: "Despliegue de solucion de cifrado para proteger datos sensibles en transito y en reposo.",
    results: ["Cifrado AES-256 implementado", "Gestion centralizada de claves", "Cumplimiento GDPR"],
    tags: ["Cifrado", "Datos", "GDPR"]
  }
]

export function CaseStudiesSection() {
  return (
    <section id="casos" className="px-6 lg:px-12 py-20 lg:py-28 border-t border-border bg-card">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <p className="text-primary text-sm font-medium uppercase tracking-wider mb-3">
            Casos de Estudio
          </p>
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4 text-balance">
            Proyectos reales, resultados medibles
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto text-pretty">
            Explora como hemos ayudado a empresas como la tuya a fortalecer su postura de seguridad.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {caseStudies.map((study, index) => (
            <article 
              key={index}
              className="group bg-background border border-border rounded-lg p-6 hover:border-primary/50 transition-colors"
            >
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                  <study.icon className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <p className="text-xs text-primary font-medium uppercase tracking-wider mb-1">
                    {study.category}
                  </p>
                  <h3 className="text-lg font-semibold text-foreground">
                    {study.title}
                  </h3>
                </div>
              </div>

              <p className="text-muted-foreground text-sm mb-4 leading-relaxed">
                {study.description}
              </p>

              <div className="mb-4">
                <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">
                  Resultados
                </p>
                <ul className="space-y-1.5">
                  {study.results.map((result, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-foreground">
                      <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                      {result}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="flex flex-wrap gap-2">
                {study.tags.map((tag, i) => (
                  <span 
                    key={i}
                    className="px-2 py-1 text-xs rounded bg-secondary text-muted-foreground"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>

        <div className="text-center mt-12">
          <Button variant="outline" asChild className="border-border text-foreground hover:bg-background">
            <Link href="/blog">
              Ver todos los casos
              <ArrowRight className="w-4 h-4 ml-2" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  )
}
