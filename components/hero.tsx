import { Lock, ChevronRight, ShieldCheck, Server, Eye } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"

export function HeroSection() {
  return (
    <section className="px-6 lg:px-12 py-20 lg:py-32 relative overflow-hidden">
      {/* Background subtle grid */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(59,130,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.03)_1px,transparent_1px)] bg-[size:60px_60px]" />
      
      <div className="max-w-5xl mx-auto text-center relative">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-card border border-border text-sm text-muted-foreground mb-8">
          <Lock className="w-4 h-4 text-primary" />
          <span>Proteccion empresarial de nivel avanzado</span>
        </div>
        
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-foreground mb-6 leading-tight text-balance">
          Ciberseguridad para{" "}
          <span className="text-primary">PyMEs</span>{" "}
          que no pueden permitirse vulnerabilidades
        </h1>
        
        <p className="text-muted-foreground text-lg md:text-xl mb-10 max-w-2xl mx-auto leading-relaxed text-pretty">
          Auditorias de seguridad, analisis de infraestructura y proteccion de datos. 
          Soluciones adaptadas a tu presupuesto y necesidades especificas.
        </p>
        
        <div className="flex flex-col sm:flex-row justify-center gap-4 mb-16">
          <Button size="lg" asChild className="bg-primary text-primary-foreground hover:bg-primary/90">
            <Link href="#contacto">
              Solicitar Auditoria
              <ChevronRight className="w-4 h-4 ml-2" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" asChild className="border-border text-foreground hover:bg-card">
            <Link href="#casos">
              Ver Casos de Estudio
            </Link>
          </Button>
        </div>

        {/* Feature highlights */}
        <div className="flex flex-wrap justify-center gap-8 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-primary" />
            <span>Auditorias Completas</span>
          </div>
          <div className="flex items-center gap-2">
            <Server className="w-5 h-5 text-primary" />
            <span>Infraestructura Segura</span>
          </div>
          <div className="flex items-center gap-2">
            <Eye className="w-5 h-5 text-primary" />
            <span>Monitoreo Continuo</span>
          </div>
        </div>
      </div>
    </section>
  )
}

export function TrustedBySection() {
  const companies = [
    "TechCorp",
    "DataSafe",
    "InnovatePyme",
    "SecureNet",
    "CloudFirst"
  ]

  return (
    <section className="px-6 lg:px-12 py-16 border-t border-border">
      <div className="max-w-6xl mx-auto text-center">
        <p className="text-muted-foreground text-sm uppercase tracking-wider mb-8">
          Empresas que confian en nuestra experiencia
        </p>
        <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16">
          {companies.map((company, i) => (
            <div 
              key={i} 
              className="text-muted-foreground/50 font-medium text-lg hover:text-muted-foreground transition-colors"
            >
              {company}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
