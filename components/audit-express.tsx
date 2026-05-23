import { CheckCircle, ArrowRight, Zap } from "lucide-react"

const auditFeatures = [
  "Analisis de perimetro y superficie de ataque",
  "Revision de politicas de acceso y privilegios",
  "Evaluacion de autenticacion web (cookies, tokens, sesiones)",
  "Identificacion de debilidades en Firewalls y ACLs",
  "Reporte de remediacion con prioridades claras",
]

export function AuditExpressSection() {
  return (
    <section id="audit-express" className="px-4 sm:px-6 lg:px-8 py-20 bg-surface-3">
      <div className="max-w-7xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left: Content */}
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 border border-primary text-primary font-mono text-xs mb-6">
              <Zap className="w-3 h-3" />
              SERVICIO RÁPIDO
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
              Audit Express
            </h2>
            <p className="text-muted-foreground mb-8 max-w-lg">
              Evaluación rápida de seguridad para empresas que necesitan saber su estado actual sin comprometer semanas de análisis. Resultados en 48-72 horas.
            </p>

            {/* Features List */}
            <ul className="space-y-3 mb-8">
              {auditFeatures.map((feature, i) => (
                <li key={i} className="flex items-center gap-3">
                  <CheckCircle className="w-4 h-4 text-primary flex-shrink-0" />
                  <span className="text-sm text-foreground">{feature}</span>
                </li>
              ))}
            </ul>

            {/* CTA */}
            <a
              href="#contacto"
              className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground font-mono text-sm font-medium hover:opacity-90 transition-opacity"
            >
              SOLICITAR AUDIT EXPRESS
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>

          {/* Right: Visual */}
          <div className="border border-border bg-surface-1 p-6">
            <div className="font-mono text-xs text-muted-foreground mb-4">// PROCESO AUDIT EXPRESS</div>
            <div className="space-y-4">
              {[
                { step: "01", label: "INTAKE", desc: "Recopilación de información inicial" },
                { step: "02", label: "SCAN", desc: "Análisis automatizado + manual" },
                { step: "03", label: "ANALYZE", desc: "Evaluación de hallazgos" },
                { step: "04", label: "REPORT", desc: "Entrega de informe ejecutivo" },
              ].map((item, i) => (
                <div key={i} className="flex items-start gap-4 p-4 border border-border hover:border-primary transition-colors">
                  <span className="font-mono text-2xl font-bold text-primary/30">{item.step}</span>
                  <div>
                    <span className="font-mono text-sm text-primary">{item.label}</span>
                    <p className="text-sm text-muted-foreground mt-1">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
