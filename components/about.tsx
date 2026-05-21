import { CheckCircle } from 'lucide-react';

const values = [
  {
    title: 'TRANSPARENCIA',
    description: 'Reportes claros, métricas reales, sin suavizar hallazgos críticos.',
  },
  {
    title: 'EFECTIVIDAD',
    description: 'Soluciones implementables que se adaptan a tu presupuesto y operaciones.',
  },
  {
    title: 'CONTINUIDAD',
    description: 'Acompañamiento post-auditoría en la implementación y validación de controles.',
  },
  {
    title: 'ÉTICA ESTRICTA',
    description: 'Confidencialidad absoluta y responsabilidad en todo hallazgo descubierto.',
  },
];

const stats = [
  { label: 'AÑOS DE EXPERIENCIA', value: '10+' },
  { label: 'EMPRESAS PROTEGIDAS', value: '50+' },
  { label: 'AUDITORÍAS COMPLETADAS', value: '100+' },
  { label: 'VULNERABILIDADES IDENTIFICADAS', value: '500+' },
];

export function AboutSection() {
  return (
    <section id="sobre" className="px-4 sm:px-6 lg:px-8 py-20 bg-background border-b border-foreground">
      <div className="max-w-7xl mx-auto">
        <div className="mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold text-foreground font-mono mb-4">SOBRE CIPHER.AR</h2>
          <div className="w-16 h-1 bg-foreground mb-6"></div>
        </div>

        {/* Mission Statement */}
        <div className="mb-20 pb-12 border-b border-foreground">
          <p className="text-xl font-mono text-foreground/80 max-w-4xl leading-relaxed">
            Cipher.ar existe para dar a las PyMEs las herramientas y conocimiento necesarios para defenderse de amenazas digitales reales.
            No vendemos miedo ni soluciones genéricas. Hacemos auditorías profundas y entregamos planes de acción implementables.
            Con más de una década de experiencia, protegemos infraestructuras críticas con métodos comprobados y transparencia absoluta.
          </p>
        </div>

        {/* Values Grid */}
        <div className="mb-20">
          <h3 className="text-2xl font-bold text-foreground font-mono mb-8">VALORES FUNDAMENTALES</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {values.map((value, i) => (
              <div key={i} className="border border-foreground p-6 bg-background hover:bg-foreground hover:text-background transition-all">
                <div className="flex items-start gap-3 mb-3">
                  <CheckCircle className="w-6 h-6 flex-shrink-0 mt-0" />
                  <h4 className="text-lg font-bold font-mono">{value.title}</h4>
                </div>
                <p className="text-foreground/70 hover:text-background/80 text-sm leading-relaxed">{value.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Stats */}
        <div>
          <h3 className="text-2xl font-bold text-foreground font-mono mb-8">NÚMEROS QUE HABLAN</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 border border-foreground p-8 bg-background">
            {stats.map((stat, i) => (
              <div key={i} className="text-center border-r border-foreground/20 last:border-r-0">
                <div className="text-3xl font-bold text-foreground font-mono mb-2">{stat.value}</div>
                <div className="text-xs text-foreground/60 font-mono uppercase tracking-widest">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export function TeamSection() {
  return (
    <section className="px-4 sm:px-6 lg:px-8 py-20 bg-background border-b border-foreground">
      <div className="max-w-7xl mx-auto">
        <h3 className="text-2xl font-bold text-foreground font-mono mb-8">EQUIPO</h3>
        <div className="border border-foreground p-8 bg-background">
          <h4 className="text-xl font-bold font-mono text-foreground mb-2">Guillermo A. Fernández</h4>
          <p className="text-sm text-foreground/60 font-mono uppercase tracking-widest mb-4">Founder & Security Architect</p>
          <p className="text-foreground/70 leading-relaxed">
            Especialista en ciberseguridad con 10+ años auditando infraestructuras críticas. Experto en análisis de riesgos,
            respuesta a incidentes y diseño de arquitecturas seguras. Certificado en seguridad ofensiva y defensiva,
            ha protegido empresas de todos los tamaños contra amenazas reales y emergentes.
          </p>
        </div>
      </div>
    </section>
  );
}
