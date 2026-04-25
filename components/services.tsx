import { 
  Shield, 
  Network, 
  FileSearch, 
  Lock, 
  Server, 
  AlertTriangle,
  ChevronRight
} from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"

const services = [
  {
    icon: FileSearch,
    title: "Auditoria de Seguridad",
    description: "Evaluacion exhaustiva de tu infraestructura, identificando vulnerabilidades y riesgos antes de que sean explotados.",
    features: ["Analisis de red y sistemas", "Pruebas de penetracion", "Informe ejecutivo detallado"]
  },
  {
    icon: Network,
    title: "Seguridad de Red",
    description: "Diseno e implementacion de arquitecturas de red seguras, segmentacion y control de acceso.",
    features: ["Configuracion de firewalls", "VPNs y acceso remoto seguro", "Segmentacion de redes WiFi"]
  },
  {
    icon: Shield,
    title: "Proteccion de Datos",
    description: "Estrategias de proteccion de informacion sensible, cumplimiento normativo y respaldo seguro.",
    features: ["Cifrado de datos", "Politicas de acceso", "Backup y recuperacion"]
  },
  {
    icon: Server,
    title: "Infraestructura Segura",
    description: "Hardening de servidores, actualizaciones de seguridad y configuracion de sistemas operativos.",
    features: ["Hardening de servidores", "Gestion de parches", "Configuracion segura"]
  },
  {
    icon: AlertTriangle,
    title: "Respuesta a Incidentes",
    description: "Planes de accion ante brechas de seguridad, contencion de danos y recuperacion operativa.",
    features: ["Plan de contingencia", "Analisis forense", "Recuperacion rapida"]
  },
  {
    icon: Lock,
    title: "Consultoria y Capacitacion",
    description: "Formacion para tu equipo en mejores practicas de seguridad y concienciacion ante amenazas.",
    features: ["Talleres presenciales", "Simulaciones de phishing", "Politicas de seguridad"]
  }
]

export function ServicesSection() {
  return (
    <section id="servicios" className="px-6 lg:px-12 py-20 lg:py-28 border-t border-border">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <p className="text-primary text-sm font-medium uppercase tracking-wider mb-3">
            Nuestros Servicios
          </p>
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4 text-balance">
            Soluciones de seguridad adaptadas a tu empresa
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto text-pretty">
            Desde auditorias iniciales hasta implementacion completa, 
            te acompanamos en cada paso hacia una infraestructura mas segura.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {services.map((service, index) => (
            <div 
              key={index}
              className="group bg-card border border-border rounded-lg p-6 hover:border-primary/50 transition-colors"
            >
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                <service.icon className="w-6 h-6 text-primary" />
              </div>
              
              <h3 className="text-xl font-semibold text-foreground mb-2">
                {service.title}
              </h3>
              
              <p className="text-muted-foreground text-sm mb-4 leading-relaxed">
                {service.description}
              </p>
              
              <ul className="space-y-2">
                {service.features.map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-muted-foreground">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="text-center mt-12">
          <Button size="lg" asChild className="bg-primary text-primary-foreground hover:bg-primary/90">
            <Link href="#contacto">
              Solicitar Informacion
              <ChevronRight className="w-4 h-4 ml-2" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  )
}
