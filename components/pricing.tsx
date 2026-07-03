import { Check, Minus } from "lucide-react"

const tiers = [
  {
    name: "FREE",
    price: "$0",
    desc: "Para equipos pequeños que quieren empezar a fortalecer su seguridad.",
    features: [
      { included: true, text: "1 activo monitoreado" },
      { included: true, text: "Escaneo mensual de superficie" },
      { included: true, text: "Simulación de phishing básica" },
      { included: true, text: "Reportes por email" },
      { included: false, text: "Alertas en tiempo real" },
      { included: false, text: "API access" },
      { included: false, text: "Soporte prioritario" },
    ],
    cta: "Comenzar gratis",
    href: "/register",
  },
  {
    name: "PRO",
    price: "$99",
    period: "/mes",
    desc: "Para empresas que necesitan monitoreo continuo y simulación avanzada.",
    popular: true,
    features: [
      { included: true, text: "Activos ilimitados" },
      { included: true, text: "Escaneo continuo 24/7" },
      { included: true, text: "Campañas de phishing ilimitadas" },
      { included: true, text: "Alertas en tiempo real (Slack/Email/Webhook)" },
      { included: true, text: "API access" },
      { included: true, text: "Dashboard avanzado con analytics" },
      { included: false, text: "Soporte prioritario" },
    ],
    cta: "Empezar prueba gratuita",
    href: "/register",
  },
  {
    name: "ENTERPRISE",
    price: "Custom",
    desc: "Para organizaciones con necesidades específicas de seguridad y compliance.",
    features: [
      { included: true, text: "Todo lo de Pro" },
      { included: true, text: "On-premise deployment" },
      { included: true, text: "SSO / SAML" },
      { included: true, text: "SLA personalizado" },
      { included: true, text: "Soporte prioritario 24/7" },
      { included: true, text: "Auditoría y compliance" },
      { included: true, text: "Customer Success dedicado" },
    ],
    cta: "Contactar ventas",
    href: "#contacto",
  },
]

export function PricingSection() {
  return (
    <section id="pricing" className="px-4 sm:px-6 lg:px-8 py-20 bg-surface-2">
      <div className="max-w-7xl mx-auto">
        <div className="max-w-2xl mx-auto text-center mb-16">
          <span className="font-mono text-xs text-primary tracking-[0.2em]">PRICING</span>
          <h2 className="font-mono text-3xl sm:text-4xl font-bold mt-4 mb-4">
            PLANES<span className="text-primary">_</span>
          </h2>
          <p className="text-muted-foreground font-mono text-sm leading-relaxed">
            Sin sorpresas ni cargos ocultos. Todos los planes incluyen actualizaciones y
            soporte técnico.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-px bg-border">
          {tiers.map((tier) => (
            <div
              key={tier.name}
              className={`relative bg-surface-1 p-8 flex flex-col ${
                tier.popular ? "border border-primary" : ""
              }`}
            >
              {tier.popular && (
                <span className="absolute -top-3 left-8 font-mono text-xs bg-primary text-background px-3 py-1">
                  MÁS POPULAR
                </span>
              )}
              <div className="mb-8">
                <h3 className="font-mono text-sm text-primary tracking-wider mb-2">
                  {tier.name}
                </h3>
                <div className="flex items-baseline gap-1">
                  <span className="font-mono text-4xl font-bold">{tier.price}</span>
                  {tier.period && (
                    <span className="font-mono text-sm text-muted-foreground">
                      {tier.period}
                    </span>
                  )}
                </div>
                <p className="font-mono text-xs text-muted-foreground mt-3">
                  {tier.desc}
                </p>
              </div>

              <ul className="space-y-3 mb-8 flex-1">
                {tier.features.map((feature) => (
                  <li key={feature.text} className="flex items-start gap-3">
                    {feature.included ? (
                      <Check className="text-primary mt-0.5 flex-shrink-0" size={14} />
                    ) : (
                      <Minus className="text-muted-foreground mt-0.5 flex-shrink-0" size={14} />
                    )}
                    <span
                      className={`font-mono text-xs ${
                        feature.included ? "text-foreground" : "text-muted-foreground"
                      }`}
                    >
                      {feature.text}
                    </span>
                  </li>
                ))}
              </ul>

              <a
                href={tier.href}
                className={`block text-center font-mono text-sm border px-6 py-3 transition-colors ${
                  tier.popular
                    ? "border-primary bg-primary text-background hover:bg-primary/90"
                    : "border-border text-foreground hover:border-primary hover:text-primary"
                }`}
              >
                {tier.cta}
              </a>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
