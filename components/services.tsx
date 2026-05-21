import { Lock, Network, Database, Server, AlertTriangle, MessageSquare } from 'lucide-react';

const services = [
  {
    icon: Lock,
    title: 'AUDITORÍA DE SEGURIDAD',
    description: 'Análisis profundo de vulnerabilidades, evaluación de controles y pruebas de penetración en tu infraestructura.',
  },
  {
    icon: Network,
    title: 'SEGURIDAD DE REDES',
    description: 'Configuración segura de firewalls, VPNs, segmentación de red y políticas de acceso basadas en principios zero-trust.',
  },
  {
    icon: Database,
    title: 'PROTECCIÓN DE DATOS',
    description: 'Implementación de cifrado, gestión de accesos, cumplimiento normativo y estrategias de backup y disaster recovery.',
  },
  {
    icon: Server,
    title: 'HARDENING DE INFRAESTRUCTURA',
    description: 'Fortalecimiento de servidores, aplicaciones y sistemas operativos contra ataques conocidos y emergentes.',
  },
  {
    icon: AlertTriangle,
    title: 'RESPUESTA A INCIDENTES',
    description: 'Investigación post-incidente, contención de amenazas y planes de remediación inmediata.',
  },
  {
    icon: MessageSquare,
    title: 'CONSULTORÍA ESTRATÉGICA',
    description: 'Roadmaps de seguridad, política de gestión de riesgos y capacitación al equipo en buenas prácticas.',
  },
];

export function ServicesSection() {
  return (
    <section id="servicios" className="px-4 sm:px-6 lg:px-8 py-20 bg-background border-b border-foreground">
      <div className="max-w-7xl mx-auto">
        <div className="mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold text-foreground font-mono mb-4">SERVICIOS</h2>
          <div className="w-16 h-1 bg-foreground mb-6"></div>
          <p className="text-lg text-foreground/70 font-mono max-w-2xl">
            Soluciones completas de ciberseguridad adaptadas al tamaño y necesidades específicas de tu empresa.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {services.map((service, i) => {
            const Icon = service.icon;
            return (
              <div
                key={i}
                className="bg-background border border-foreground p-8 hover:bg-foreground hover:text-background transition-all group"
              >
                <Icon className="w-8 h-8 text-foreground mb-4 group-hover:text-background" />
                <h3 className="text-lg font-bold font-mono mb-3 text-foreground group-hover:text-background">
                  {service.title}
                </h3>
                <p className="text-foreground/70 group-hover:text-background/80 text-sm leading-relaxed">
                  {service.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
