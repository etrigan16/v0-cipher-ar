const cases = [
  {
    title: 'RED WIFI EMPRESARIAL CON SEGMENTACIÓN',
    scenario: 'PyME con 30 empleados sin controles de acceso WiFi',
    problem: 'Invitados y empleados en la misma red, acceso a datos sensibles sin autenticación.',
    solution: 'Implementamos WiFi dual: red corporativa con WPA3 y VLAN segura para invitados, MFA en accesos administrativos.',
    result: '100% aislamiento de tráfico, auditorías sin hallazgos críticos.',
  },
  {
    title: 'HARDENING DE SERVIDORES',
    scenario: 'Empresa con servidor Windows sin actualizar desde 2020',
    problem: 'Vulnerabilidades conocidas explotables, sin firewall local, puertos innecesarios abiertos.',
    solution: 'Auditoría de configuración, cierre de puertos, hardening de SO, implementación de Windows Defender con exclusiones mínimas.',
    result: 'Reducción del 95% de superficie de ataque, cumplimiento de estándares de seguridad.',
  },
  {
    title: 'ANÁLISIS DE VULNERABILIDADES CRÍTICAS',
    scenario: 'Aplicación web interna expuesta a internet sin validación',
    problem: 'SQL injection, XSS, ausencia de CORS, credenciales hardcodeadas en código.',
    solution: 'Pruebas de penetración, reporte detallado con PoC, implementación de WAF y validación de entradas.',
    result: '5 vulnerabilidades críticas corregidas, aplicación deployable en producción segura.',
  },
  {
    title: 'CIFRADO Y BACKUP SEGURO',
    scenario: 'Empresa sin estrategia de backup, datos en servidores sin encriptar',
    problem: 'Riesgo total de pérdida de datos por ransomware o fallo hardware, cumplimiento incorrecto de RGPD.',
    solution: 'Implementación de BitLocker en servidores, backup automatizado con encriptación AES-256, plan de disaster recovery.',
    result: 'RPO de 4 horas, RTO de 2 horas, cumplimiento total de normativa de datos.',
  },
];

export function CaseStudiesSection() {
  return (
    <section id="casos" className="px-4 sm:px-6 lg:px-8 py-20 bg-background border-b border-foreground">
      <div className="max-w-7xl mx-auto">
        <div className="mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold text-foreground font-mono mb-4">CASOS DE ESTUDIO</h2>
          <div className="w-16 h-1 bg-foreground mb-6"></div>
          <p className="text-lg text-foreground/70 font-mono max-w-2xl">
            Ejemplos reales de cómo identificamos y corregimos vulnerabilidades en empresas como la tuya.
          </p>
        </div>

        <div className="space-y-6">
          {cases.map((caseItem, i) => (
            <div key={i} className="border border-foreground p-8 bg-background hover:bg-foreground hover:text-background transition-all">
              <h3 className="text-xl font-bold font-mono text-foreground hover:text-background mb-4">{caseItem.title}</h3>

              <div className="space-y-3 text-sm">
                <div>
                  <span className="font-mono text-foreground/60 hover:text-background/60">ESCENARIO:</span>
                  <p className="text-foreground/80 hover:text-background/80">{caseItem.scenario}</p>
                </div>

                <div>
                  <span className="font-mono text-foreground/60 hover:text-background/60">PROBLEMA:</span>
                  <p className="text-foreground/80 hover:text-background/80">{caseItem.problem}</p>
                </div>

                <div>
                  <span className="font-mono text-foreground/60 hover:text-background/60">SOLUCIÓN:</span>
                  <p className="text-foreground/80 hover:text-background/80">{caseItem.solution}</p>
                </div>

                <div>
                  <span className="font-mono text-foreground/60 hover:text-background/60">RESULTADO:</span>
                  <p className="text-foreground font-bold hover:text-background">{caseItem.result}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
