import { ArrowRight, Shield } from 'lucide-react';
import Link from 'next/link';

export function HeroSection() {
  return (
    <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8 bg-background border-b border-foreground">
      <div className="max-w-7xl mx-auto">
        {/* Main Heading */}
        <div className="mb-12">
          <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold text-foreground font-mono leading-tight mb-6">
            CIBERSEGURIDAD
            <br />
            TÁCTICA
          </h1>
          <div className="border-t-2 border-foreground w-32 my-6"></div>
          <p className="text-lg sm:text-xl text-foreground/80 font-mono max-w-2xl leading-relaxed">
            Auditorías de seguridad, análisis de riesgos e implementación de protecciones para empresas que
            necesitan defender su infraestructura digital. Sin bordes suavizados, sin marketing hueco.
            <span className="text-foreground/60"> Solo soluciones.</span>
          </p>
        </div>

        {/* Stats Line */}
        <div className="flex flex-wrap gap-8 mb-12 border-t border-b border-foreground py-6">
          <div>
            <div className="text-sm text-foreground/60 font-mono">SERVICIOS ACTIVOS</div>
            <div className="text-2xl text-foreground font-bold font-mono">6+</div>
          </div>
          <div>
            <div className="text-sm text-foreground/60 font-mono">AUDITORÍAS COMPLETADAS</div>
            <div className="text-2xl text-foreground font-bold font-mono">50+</div>
          </div>
          <div>
            <div className="text-sm text-foreground/60 font-mono">VULNERABILIDADES DESCUBIERTAS</div>
            <div className="text-2xl text-foreground font-bold font-mono">200+</div>
          </div>
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4">
          <Link
            href="#contacto"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-foreground text-background font-bold font-mono border border-foreground hover:opacity-80 transition-opacity"
          >
            <Shield size={20} />
            SOLICITAR AUDITORÍA
            <ArrowRight size={20} />
          </Link>
          <Link
            href="#riesgos"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-background text-foreground border border-foreground font-bold font-mono hover:bg-foreground hover:text-background transition-all"
          >
            EVALUAR RIESGOS
          </Link>
        </div>
      </div>
    </section>
  );
}

export function TrustedBySection() {
  const companies = ['TechCorp', 'DataSafe', 'InnovatePyme', 'SecureNet', 'CloudFirst'];

  return (
    <section className="px-4 sm:px-6 lg:px-8 py-16 border-t border-foreground bg-background">
      <div className="max-w-7xl mx-auto text-center">
        <p className="text-foreground/60 text-sm uppercase tracking-widest font-mono mb-8">
          EMPRESAS QUE CONFÍAN EN CIPHER.AR
        </p>
        <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16">
          {companies.map((company, i) => (
            <div key={i} className="text-foreground/40 font-mono text-lg hover:text-foreground/70 transition-colors">
              {company}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
