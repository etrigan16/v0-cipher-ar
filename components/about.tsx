import { Award, Users, Clock, Target } from "lucide-react"

const stats = [
  { icon: Award, value: "10+", label: "Anos de experiencia" },
  { icon: Users, value: "50+", label: "Clientes protegidos" },
  { icon: Clock, value: "24/7", label: "Monitoreo disponible" },
  { icon: Target, value: "100%", label: "Compromiso" }
]

const values = [
  {
    title: "Integridad",
    description: "Actuamos con honestidad y transparencia en cada proyecto, manteniendo la confidencialidad de tu informacion."
  },
  {
    title: "Excelencia",
    description: "Buscamos la mejora continua y aplicamos las mejores practicas de la industria en cada solucion."
  },
  {
    title: "Compromiso",
    description: "Tu seguridad es nuestra prioridad. Nos involucramos profundamente en cada proyecto hasta alcanzar los objetivos."
  }
]

export function AboutSection() {
  return (
    <section id="nosotros" className="px-6 lg:px-12 py-20 lg:py-28 border-t border-border">
      <div className="max-w-6xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Content */}
          <div>
            <p className="text-primary text-sm font-medium uppercase tracking-wider mb-3">
              Sobre Nosotros
            </p>
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-6 text-balance">
              Expertos en proteger lo que mas importa: tu negocio
            </h2>
            <div className="space-y-4 text-muted-foreground leading-relaxed">
              <p>
                Con mas de una decada de experiencia en ciberseguridad, nos especializamos en 
                proteger pequenas y medianas empresas de las amenazas digitales que enfrentan hoy.
              </p>
              <p>
                Entendemos que cada empresa es unica. Por eso, no ofrecemos soluciones genericas. 
                Analizamos tu infraestructura, identificamos riesgos especificos y disenamos 
                estrategias de seguridad que se adaptan a tu presupuesto y necesidades.
              </p>
              <p>
                Nuestro enfoque combina tecnologia de vanguardia con un profundo conocimiento 
                del panorama de amenazas actual, garantizando que tu empresa este preparada 
                para enfrentar cualquier desafio de seguridad.
              </p>
            </div>
          </div>

          {/* Values */}
          <div className="space-y-6">
            {values.map((value, index) => (
              <div 
                key={index}
                className="bg-card border border-border rounded-lg p-6"
              >
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  {value.title}
                </h3>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  {value.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-16 pt-16 border-t border-border">
          {stats.map((stat, index) => (
            <div key={index} className="text-center">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mx-auto mb-4">
                <stat.icon className="w-6 h-6 text-primary" />
              </div>
              <div className="text-3xl font-bold text-foreground mb-1">
                {stat.value}
              </div>
              <div className="text-sm text-muted-foreground">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

interface TeamMember {
  name: string
  role: string
  bio: string
}

const teamMembers: TeamMember[] = [
  {
    name: "Guillermo A. Fernandez",
    role: "Director de Seguridad",
    bio: "Especialista en seguridad de redes con mas de 10 anos de experiencia protegiendo infraestructuras criticas."
  }
]

export function TeamSection() {
  return (
    <section className="px-6 lg:px-12 py-20 lg:py-28 border-t border-border bg-card">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <p className="text-primary text-sm font-medium uppercase tracking-wider mb-3">
            Nuestro Equipo
          </p>
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4 text-balance">
            Profesionales comprometidos con tu seguridad
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Un equipo de expertos dedicados a proteger tu empresa.
          </p>
        </div>

        <div className="flex justify-center">
          {teamMembers.map((member, index) => (
            <div 
              key={index}
              className="bg-background border border-border rounded-lg p-8 max-w-md text-center"
            >
              <div className="w-24 h-24 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl font-bold text-primary">
                  {member.name.split(' ').map(n => n[0]).join('')}
                </span>
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-1">
                {member.name}
              </h3>
              <p className="text-primary text-sm mb-4">
                {member.role}
              </p>
              <p className="text-muted-foreground text-sm leading-relaxed">
                {member.bio}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
