const testimonials = [
  {
    name: 'Juan Pérez',
    company: 'Tech Solutions SA',
    role: 'Director de IT',
    text: 'La auditoría de Cipher.ar identificó vulnerabilidades críticas que no habíamos detectado. El equipo fue profesional, transparente y entregó un plan implementable. Nuestras defensas mejoraron significativamente.',
  },
  {
    name: 'María González',
    company: 'Marketing Digital Pro',
    role: 'Gerente General',
    text: 'Después del ataque ransomware, Cipher.ar nos ayudó a recuperarnos y fortalecer toda nuestra infraestructura. Ahora tenemos monitoreo 24/7. Pueden confiar en ellos.',
  },
  {
    name: 'Carlos López',
    company: 'E-commerce Latam',
    role: 'CTO',
    text: 'El hardening de nuestros servidores y la implementación de cifrado de datos fue impecable. Cumplimos con GDPR sin complicaciones. El soporte post-implementación es excelente.',
  },
];

export function TestimonialsSection() {
  return (
    <section className="px-4 sm:px-6 lg:px-8 py-20 bg-background border-b border-foreground">
      <div className="max-w-7xl mx-auto">
        <h2 className="text-4xl sm:text-5xl font-bold text-foreground font-mono mb-4">TESTIMONIOS</h2>
        <div className="w-16 h-1 bg-foreground mb-12"></div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {testimonials.map((testimonial, i) => (
            <div key={i} className="border border-foreground p-8 bg-background hover:bg-foreground hover:text-background transition-all">
              <p className="text-sm mb-6 leading-relaxed italic">"{testimonial.text}"</p>
              <div className="border-t border-foreground/20 hover:border-background/20 pt-4">
                <p className="font-bold font-mono text-foreground hover:text-background">{testimonial.name}</p>
                <p className="text-sm text-foreground/60 hover:text-background/60 font-mono">{testimonial.role}</p>
                <p className="text-sm text-foreground/60 hover:text-background/60">{testimonial.company}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
