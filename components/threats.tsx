import { 
  Bug, 
  Mail, 
  Wifi, 
  Database, 
  Key, 
  Globe,
  AlertTriangle,
  ArrowRight
} from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"

const threats = [
  {
    icon: Mail,
    name: "Phishing",
    severity: "Alto",
    description: "Ataques de ingenieria social mediante correos fraudulentos que buscan robar credenciales o instalar malware.",
    prevention: "Capacitacion de empleados, filtros de correo, autenticacion multifactor."
  },
  {
    icon: Bug,
    name: "Ransomware",
    severity: "Critico",
    description: "Software malicioso que cifra archivos y exige rescate. Puede paralizar operaciones por dias o semanas.",
    prevention: "Backups regulares, segmentacion de red, EDR/Antivirus actualizado."
  },
  {
    icon: Wifi,
    name: "Ataques WiFi",
    severity: "Medio",
    description: "Interceptacion de trafico en redes inalambricas mal configuradas. Robo de datos en transito.",
    prevention: "WPA3, redes separadas para invitados, VPN para acceso remoto."
  },
  {
    icon: Database,
    name: "SQL Injection",
    severity: "Alto",
    description: "Explotacion de vulnerabilidades en aplicaciones web para acceder a bases de datos.",
    prevention: "Consultas parametrizadas, WAF, auditorias de codigo regulares."
  },
  {
    icon: Key,
    name: "Credenciales Comprometidas",
    severity: "Alto",
    description: "Uso de contrasenas robadas o debiles para acceder a sistemas criticos.",
    prevention: "Politicas de contrasenas fuertes, MFA, gestion de identidades."
  },
  {
    icon: Globe,
    name: "DDoS",
    severity: "Medio",
    description: "Ataques de denegacion de servicio que saturan servidores e impiden acceso legitimo.",
    prevention: "CDN con proteccion DDoS, rate limiting, arquitectura redundante."
  }
]

const vulnerabilities = [
  {
    title: "Software Desactualizado",
    description: "El 60% de las brechas explotan vulnerabilidades con parches disponibles.",
    action: "Implementar gestion automatizada de parches"
  },
  {
    title: "Configuraciones por Defecto",
    description: "Contrasenas y configuraciones de fabrica facilitan el acceso no autorizado.",
    action: "Auditar y endurecer todas las configuraciones"
  },
  {
    title: "Falta de Segmentacion",
    description: "Redes planas permiten movimiento lateral una vez comprometido un equipo.",
    action: "Implementar VLANs y microsegmentacion"
  },
  {
    title: "Sin Monitoreo",
    description: "Sin visibilidad, los ataques pueden pasar desapercibidos durante meses.",
    action: "Implementar SIEM y alertas en tiempo real"
  }
]

function SeverityBadge({ severity }: { severity: string }) {
  const colors = {
    Critico: "bg-red-500/20 text-red-400 border-red-500/30",
    Alto: "bg-orange-500/20 text-orange-400 border-orange-500/30",
    Medio: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
  }
  
  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded border ${colors[severity as keyof typeof colors]}`}>
      {severity}
    </span>
  )
}

export function ThreatsSection() {
  return (
    <section id="amenazas" className="px-6 lg:px-12 py-20 lg:py-28 border-t border-border">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <p className="text-primary text-sm font-medium uppercase tracking-wider mb-3">
            Amenazas Actuales
          </p>
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4 text-balance">
            Conoce los riesgos que enfrenta tu empresa
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto text-pretty">
            Mantente informado sobre las amenazas mas comunes y como protegerte de ellas.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          {threats.map((threat, index) => (
            <div 
              key={index}
              className="bg-card border border-border rounded-lg p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <threat.icon className="w-5 h-5 text-primary" />
                </div>
                <SeverityBadge severity={threat.severity} />
              </div>

              <h3 className="text-lg font-semibold text-foreground mb-2">
                {threat.name}
              </h3>
              
              <p className="text-muted-foreground text-sm mb-4 leading-relaxed">
                {threat.description}
              </p>

              <div className="pt-4 border-t border-border">
                <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
                  Prevencion
                </p>
                <p className="text-sm text-foreground">
                  {threat.prevention}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Vulnerabilities */}
        <div className="bg-card border border-border rounded-lg p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-orange-400" />
            </div>
            <h3 className="text-xl font-semibold text-foreground">
              Vulnerabilidades Comunes en PyMEs
            </h3>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {vulnerabilities.map((vuln, index) => (
              <div key={index} className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                  <span className="text-sm font-semibold text-primary">{index + 1}</span>
                </div>
                <div>
                  <h4 className="font-medium text-foreground mb-1">
                    {vuln.title}
                  </h4>
                  <p className="text-sm text-muted-foreground mb-2">
                    {vuln.description}
                  </p>
                  <p className="text-sm text-primary">
                    {vuln.action}
                  </p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-8 pt-6 border-t border-border text-center">
            <Button asChild className="bg-primary text-primary-foreground hover:bg-primary/90">
              <Link href="#calculadora">
                Evalua tu nivel de riesgo
                <ArrowRight className="w-4 h-4 ml-2" />
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  )
}
