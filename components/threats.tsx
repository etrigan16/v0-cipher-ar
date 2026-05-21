import { AlertCircle } from 'lucide-react';

const threats = [
  {
    name: 'PHISHING Y INGENIERÍA SOCIAL',
    description: 'Emails fraudulentos que parecen legítimos para robar credenciales. Un empleado sin capacitación es tu punto débil más grande.',
    impact: 'CRÍTICO',
    mitigation: 'Capacitación regular, simulaciones de phishing, autenticación multifactor, filtros de email avanzados.',
  },
  {
    name: 'RANSOMWARE',
    description: 'Malware que encripta datos y demanda rescate. Afecta especialmente a empresas sin backup seguro.',
    impact: 'CRÍTICO',
    mitigation: 'Backups inmutables offline, detección de comportamiento anómalo, EDR en endpoints, respuesta a incidentes.',
  },
  {
    name: 'ATAQUES A REDES WIFI',
    description: 'Redes WiFi sin WPA3 o con contraseñas débiles permiten captura de tráfico y acceso no autorizado.',
    impact: 'ALTO',
    mitigation: 'WPA3 con contraseñas fuertes, segmentación de red, desactivar WPS, ocultar SSID broadcast.',
  },
  {
    name: 'SQL INJECTION Y XSS',
    description: 'Ataques a aplicaciones web que permiten acceder a bases de datos o ejecutar código malicioso en navegadores.',
    impact: 'CRÍTICO',
    mitigation: 'Validación de entradas, uso de ORMs seguros, WAF, testing de seguridad en desarrollo.',
  },
  {
    name: 'ROBO DE CREDENCIALES',
    description: 'Contraseñas débiles, reutilización de passwords, o credenciales expuestas en breaches públicos.',
    impact: 'ALTO',
    mitigation: 'Gestor de contraseñas empresarial, MFA en todos los accesos, monitoreo de credenciales en dark web.',
  },
  {
    name: 'ATAQUES DDoS',
    description: 'Saturación de servidores con tráfico masivo para causar indisponibilidad del servicio.',
    impact: 'MEDIO-ALTO',
    mitigation: 'CDN con protección DDoS, rate limiting, WAF, plan de respuesta a incidentes.',
  },
  {
    name: 'FALTA DE ACTUALIZACIONES Y PATCHES',
    description: 'Sistemas operativos y aplicaciones sin parches de seguridad, expuestos a vulnerabilidades conocidas.',
    impact: 'CRÍTICO',
    mitigation: 'Plan de parcheo automático, control de versiones, inventario de software, testing antes de deploy.',
  },
  {
    name: 'ACCESO NO AUTORIZADO A DATOS',
    description: 'Empleados o terceros con permisos excesivos o sin segmentación de red adecuada.',
    impact: 'ALTO',
    mitigation: 'Principio de menor privilegio, auditoría de permisos, VLAN segmentadas, logging de accesos.',
  },
];

const vulnerabilities = [
  'Configuración insegura de firewalls y routers',
  'Puertos abiertos innecesarios en servidores',
  'Cuentas de administrador con contraseñas por defecto',
  'Falta de cifrado en datos en tránsito y en reposo',
  'Software EOL (End of Life) sin soporte de seguridad',
  'Documentación de seguridad desactualizada o inexistente',
  'Sin monitoreo o SIEM centralizado de logs',
  'Gestión de llaves de encriptación deficiente',
];

export function ThreatsSection() {
  return (
    <section id="amenazas" className="px-4 sm:px-6 lg:px-8 py-20 bg-background border-b border-foreground">
      <div className="max-w-7xl mx-auto">
        <div className="mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold text-foreground font-mono mb-4">AMENAZAS Y VULNERABILIDADES</h2>
          <div className="w-16 h-1 bg-foreground mb-6"></div>
          <p className="text-lg text-foreground/70 font-mono max-w-2xl">
            Las amenazas reales que enfrentan las PyMEs hoy. Identifícalas en tu infraestructura.
          </p>
        </div>

        {/* Threats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-20">
          {threats.map((threat, i) => (
            <div key={i} className="border border-foreground p-6 bg-background">
              <div className="flex items-start gap-3 mb-3">
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-1 text-foreground" />
                <div>
                  <h3 className="text-lg font-bold font-mono text-foreground">{threat.name}</h3>
                  <p className="text-xs text-foreground/60 font-mono mt-1">IMPACTO: {threat.impact}</p>
                </div>
              </div>
              <p className="text-foreground/70 text-sm mb-4 leading-relaxed">{threat.description}</p>
              <p className="text-sm font-mono text-foreground/60">
                <span className="font-bold">Mitigación:</span> {threat.mitigation}
              </p>
            </div>
          ))}
        </div>

        {/* Common Vulnerabilities */}
        <div>
          <h3 className="text-2xl font-bold text-foreground font-mono mb-6">VULNERABILIDADES COMUNES EN PYMES</h3>
          <div className="border border-foreground p-8 bg-background">
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {vulnerabilities.map((vuln, i) => (
                <li key={i} className="flex items-start gap-3 text-foreground/70 text-sm">
                  <span className="text-foreground font-bold mt-1">→</span>
                  {vuln}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
