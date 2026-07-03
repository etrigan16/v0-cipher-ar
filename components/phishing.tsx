import { Siren, Users, LineChart, Shield } from "lucide-react"

const features = [
  {
    icon: Siren,
    title: "CAMPAÑAS REALISTAS",
    desc: "Simulaciones basadas en amenazas reales del panorama actual. Phishing, spear-phishing, vishing y más.",
  },
  {
    icon: Users,
    title: "TRAINING ADAPTIVO",
    desc: "Entrenamiento personalizado según el rol y nivel de riesgo de cada empleado. Contenido en español.",
  },
  {
    icon: LineChart,
    title: "ANALYTICS DETALLADO",
    desc: "Métricas de clics, reportes, y evolución temporal. Identifica a los usuarios más vulnerables.",
  },
  {
    icon: Shield,
    title: "REMEDIACIÓN AUTOMÁTICA",
    desc: "Acciones correctivas automatizadas: políticas de MFA, bloqueo de dominios sospechosos, y más.",
  },
]

export function PhishingSection() {
  return (
    <section id="phishing" className="px-4 sm:px-6 lg:px-8 py-20 bg-surface-1">
      <div className="max-w-7xl mx-auto">
        <div className="max-w-2xl mb-16">
          <span className="font-mono text-xs text-primary tracking-[0.2em]">PRODUCTO</span>
          <h2 className="font-mono text-3xl sm:text-4xl font-bold mt-4 mb-4">
            PHISHING<span className="text-primary">_</span>
            <br />
            <span className="text-muted-foreground">SIMULATION</span>
          </h2>
          <p className="text-muted-foreground font-mono text-sm leading-relaxed">
            Simulaciones de phishing realistas para medir y mejorar la resiliencia de tu
            equipo frente a ataques de ingeniería social.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-px bg-border">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="bg-surface-2 p-8 hover:bg-surface-3 transition-colors"
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
