import { Shield, Lock, ChevronRight, Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"

function Navbar() {
  return (
    <nav className="flex items-center justify-between px-6 lg:px-12 py-4 border-b border-border bg-background/80 backdrop-blur-md sticky top-0 z-50">
      <Link href="/" className="flex items-center gap-2">
        <Shield className="w-7 h-7 text-primary" />
        <span className="font-semibold text-foreground text-lg">Guillermo A. Fernandez</span>
      </Link>
      
      <div className="hidden md:flex items-center gap-8 text-sm text-muted-foreground">
        <Link href="#servicios" className="hover:text-foreground transition-colors">Servicios</Link>
        <Link href="#casos" className="hover:text-foreground transition-colors">Casos de Estudio</Link>
        <Link href="#amenazas" className="hover:text-foreground transition-colors">Amenazas</Link>
        <Link href="#nosotros" className="hover:text-foreground transition-colors">Nosotros</Link>
        <Link href="#faq" className="hover:text-foreground transition-colors">FAQ</Link>
        <Link href="#contacto" className="hover:text-foreground transition-colors">Contacto</Link>
      </div>
      
      <div className="flex items-center gap-3">
        <Button className="hidden sm:inline-flex bg-primary text-primary-foreground hover:bg-primary/90">
          Consulta Gratis
        </Button>
        <Button variant="ghost" size="icon" className="md:hidden text-foreground">
          <Menu className="w-5 h-5" />
        </Button>
      </div>
    </nav>
  )
}

function HeroSection() {
  return (
    <section className="px-6 lg:px-12 py-20 lg:py-32">
      <div className="max-w-4xl mx-auto text-center">
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
        
        <div className="flex flex-col sm:flex-row justify-center gap-4">
          <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90">
            Solicitar Auditoria
            <ChevronRight className="w-4 h-4 ml-2" />
          </Button>
          <Button size="lg" variant="outline" className="border-border text-foreground hover:bg-card">
            Ver Casos de Estudio
          </Button>
        </div>
      </div>
    </section>
  )
}

function TrustedBySection() {
  return (
    <section className="px-6 lg:px-12 py-16 border-t border-border">
      <div className="max-w-6xl mx-auto text-center">
        <p className="text-muted-foreground text-sm uppercase tracking-wider mb-8">
          Empresas que confian en nuestra experiencia
        </p>
        <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16 opacity-50">
          {["Empresa A", "Empresa B", "Empresa C", "Empresa D", "Empresa E"].map((company, i) => (
            <div key={i} className="text-muted-foreground font-medium text-lg">
              {company}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default function HomePage() {
  return (
    <main className="min-h-screen bg-background">
      <Navbar />
      <HeroSection />
      <TrustedBySection />
      
      {/* Placeholder sections - se desarrollaran a continuacion */}
      <section id="servicios" className="px-6 lg:px-12 py-20 border-t border-border">
        <div className="max-w-6xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-foreground mb-4">Servicios</h2>
          <p className="text-muted-foreground">Seccion de servicios detallados</p>
        </div>
      </section>
      
      <section id="casos" className="px-6 lg:px-12 py-20 border-t border-border bg-card">
        <div className="max-w-6xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-foreground mb-4">Casos de Estudio</h2>
          <p className="text-muted-foreground">Blog y simulaciones de proyectos</p>
        </div>
      </section>
      
      <section id="amenazas" className="px-6 lg:px-12 py-20 border-t border-border">
        <div className="max-w-6xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-foreground mb-4">Amenazas y Vulnerabilidades</h2>
          <p className="text-muted-foreground">Informacion sobre posibles amenazas</p>
        </div>
      </section>
    </main>
  )
}
