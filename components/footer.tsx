import Link from "next/link"
import { Github, Linkedin, Twitter } from "lucide-react"

export function Footer() {
  return (
    <footer className="px-4 sm:px-6 lg:px-8 py-12 bg-surface-2">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
          {/* Brand */}
          <div className="md:col-span-2">
            <Link href="/" className="flex items-center gap-0 font-mono text-xl font-bold tracking-widest select-none">
              <span className="text-foreground">AU</span>
              <span className="text-primary relative">
                K
                <span className="absolute -bottom-0.5 left-0 w-full h-px bg-primary opacity-60" />
              </span>
              <span className="text-foreground">ALABS</span>
              <span className="text-primary text-xs ml-1 opacity-70 font-normal">_</span>
            </Link>
            <p className="text-sm text-muted-foreground mt-4 max-w-sm">
              Infraestructura indómita. Software blindado. Un laboratorio táctico anti-corporativo que construye sin marketing vacío.
            </p>
            <p className="font-mono text-xs text-muted-foreground mt-4">
              contact@aukalabs.com
            </p>
          </div>

          {/* Links */}
          <div>
            <h4 className="font-mono text-xs text-muted-foreground mb-4">// NAVEGACIÓN</h4>
            <ul className="space-y-2">
              {[
                { href: "#soluciones", label: "Soluciones" },
                { href: "#intelligence", label: "Intelligence" },
                { href: "#audit-express", label: "Audit Express" },
                { href: "#contacto", label: "Contacto" },
              ].map((link) => (
                <li key={link.href}>
                  <a href={link.href} className="text-sm text-muted-foreground hover:text-primary transition-colors">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="font-mono text-xs text-muted-foreground mb-4">// LEGAL</h4>
            <ul className="space-y-2">
              {[
                { href: "#", label: "Privacidad" },
                { href: "#", label: "Términos" },
              ].map((link) => (
                <li key={link.label}>
                  <a href={link.href} className="text-sm text-muted-foreground hover:text-primary transition-colors">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div className="flex flex-col md:flex-row justify-between items-center pt-8 border-t border-border">
          <p className="font-mono text-xs text-muted-foreground">
            © {new Date().getFullYear()} Aukalabs — La seguridad no es un producto, es un proceso.
          </p>
          <div className="flex items-center gap-4 mt-4 md:mt-0">
            <a href="#" className="text-muted-foreground hover:text-primary transition-colors">
              <Github className="w-4 h-4" />
            </a>
            <a href="#" className="text-muted-foreground hover:text-primary transition-colors">
              <Linkedin className="w-4 h-4" />
            </a>
            <a href="#" className="text-muted-foreground hover:text-primary transition-colors">
              <Twitter className="w-4 h-4" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}
