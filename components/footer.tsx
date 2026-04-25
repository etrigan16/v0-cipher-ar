import { Shield } from "lucide-react"
import Link from "next/link"

const footerLinks = {
  services: [
    { label: "Auditoria de Seguridad", href: "#servicios" },
    { label: "Seguridad de Red", href: "#servicios" },
    { label: "Proteccion de Datos", href: "#servicios" },
    { label: "Respuesta a Incidentes", href: "#servicios" }
  ],
  resources: [
    { label: "Casos de Estudio", href: "#casos" },
    { label: "Amenazas Actuales", href: "#amenazas" },
    { label: "Calculadora de Riesgo", href: "#calculadora" },
    { label: "FAQ", href: "#faq" }
  ],
  company: [
    { label: "Sobre Nosotros", href: "#nosotros" },
    { label: "Contacto", href: "#contacto" }
  ]
}

export function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="px-6 lg:px-12 py-16 border-t border-border bg-background">
      <div className="max-w-6xl mx-auto">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-12 mb-12">
          {/* Brand */}
          <div className="lg:col-span-1">
            <Link href="/" className="flex items-center gap-2 mb-4">
              <Shield className="w-7 h-7 text-primary" />
              <span className="font-semibold text-foreground text-lg">Guillermo A. Fernandez</span>
            </Link>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Servicios profesionales de ciberseguridad para pequenas y medianas empresas. 
              Protegemos tu negocio de las amenazas digitales.
            </p>
          </div>

          {/* Services */}
          <div>
            <h4 className="font-semibold text-foreground mb-4">Servicios</h4>
            <ul className="space-y-2">
              {footerLinks.services.map((link, index) => (
                <li key={index}>
                  <Link 
                    href={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="font-semibold text-foreground mb-4">Recursos</h4>
            <ul className="space-y-2">
              {footerLinks.resources.map((link, index) => (
                <li key={index}>
                  <Link 
                    href={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="font-semibold text-foreground mb-4">Empresa</h4>
            <ul className="space-y-2">
              {footerLinks.company.map((link, index) => (
                <li key={index}>
                  <Link 
                    href={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div className="pt-8 border-t border-border flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-muted-foreground">
            {currentYear} Guillermo A. Fernandez. Todos los derechos reservados.
          </p>
          <div className="flex gap-6 text-sm text-muted-foreground">
            <Link href="/privacidad" className="hover:text-foreground transition-colors">
              Politica de Privacidad
            </Link>
            <Link href="/terminos" className="hover:text-foreground transition-colors">
              Terminos de Servicio
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}
