import { Quote } from "lucide-react"

const testimonials = [
  {
    quote: "Despues de la auditoria descubrimos vulnerabilidades que no sabiamos que existian. La implementacion fue rapida y ahora dormimos mas tranquilos sabiendo que nuestra informacion esta protegida.",
    author: "Carlos Martinez",
    role: "Director de TI",
    company: "Distribuidora Central"
  },
  {
    quote: "El equipo entendio perfectamente nuestras limitaciones de presupuesto y nos propuso soluciones efectivas sin comprometer la seguridad. Excelente relacion calidad-precio.",
    author: "Ana Rodriguez",
    role: "Gerente General",
    company: "Servicios Financieros SR"
  },
  {
    quote: "La segmentacion de nuestra red WiFi fue un cambio fundamental. Ahora nuestros visitantes tienen acceso a internet sin comprometer nuestros recursos internos.",
    author: "Miguel Torres",
    role: "Administrador de Sistemas",
    company: "Consultora Empresarial MT"
  }
]

export function TestimonialsSection() {
  return (
    <section className="px-6 lg:px-12 py-20 lg:py-28 border-t border-border bg-card">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <p className="text-primary text-sm font-medium uppercase tracking-wider mb-3">
            Testimonios
          </p>
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4 text-balance">
            Lo que dicen nuestros clientes
          </h2>
          <p className="text-muted-foreground text-lg">
            Empresas que confiaron en nosotros y mejoraron su seguridad.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {testimonials.map((testimonial, index) => (
            <div 
              key={index}
              className="bg-background border border-border rounded-lg p-6 flex flex-col"
            >
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Quote className="w-5 h-5 text-primary" />
              </div>
              
              <blockquote className="text-foreground leading-relaxed mb-6 flex-grow">
                &ldquo;{testimonial.quote}&rdquo;
              </blockquote>
              
              <div className="pt-4 border-t border-border">
                <p className="font-medium text-foreground">
                  {testimonial.author}
                </p>
                <p className="text-sm text-muted-foreground">
                  {testimonial.role}
                </p>
                <p className="text-sm text-primary">
                  {testimonial.company}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
