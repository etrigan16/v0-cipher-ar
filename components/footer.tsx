import Link from 'next/link';

export function Footer() {
  return (
    <footer className="px-4 sm:px-6 lg:px-8 py-12 bg-background border-t border-foreground">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-8 mb-12 pb-12 border-b border-foreground">
          {/* About */}
          <div>
            <h4 className="font-mono font-bold text-foreground mb-4">CIPHER.AR</h4>
            <p className="text-sm text-foreground/70">
              Ciberseguridad táctica para PyMEs. Auditorías profundas, soluciones reales, protección efectiva.
            </p>
          </div>

          {/* Services */}
          <div>
            <h4 className="font-mono font-bold text-foreground mb-4">SERVICIOS</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="#servicios" className="text-foreground/70 hover:text-foreground transition-colors">
                  Auditorías
                </a>
              </li>
              <li>
                <a href="#servicios" className="text-foreground/70 hover:text-foreground transition-colors">
                  Infraestructura
                </a>
              </li>
              <li>
                <a href="#servicios" className="text-foreground/70 hover:text-foreground transition-colors">
                  Respuesta a Incidentes
                </a>
              </li>
              <li>
                <a href="#servicios" className="text-foreground/70 hover:text-foreground transition-colors">
                  Consultoría
                </a>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="font-mono font-bold text-foreground mb-4">RECURSOS</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="#casos" className="text-foreground/70 hover:text-foreground transition-colors">
                  Casos de Estudio
                </a>
              </li>
              <li>
                <a href="#amenazas" className="text-foreground/70 hover:text-foreground transition-colors">
                  Amenazas
                </a>
              </li>
              <li>
                <a href="#faq" className="text-foreground/70 hover:text-foreground transition-colors">
                  FAQ
                </a>
              </li>
              <li>
                <a href="#contacto" className="text-foreground/70 hover:text-foreground transition-colors">
                  Contacto
                </a>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="font-mono font-bold text-foreground mb-4">LEGAL</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="#" className="text-foreground/70 hover:text-foreground transition-colors">
                  Privacidad
                </a>
              </li>
              <li>
                <a href="#" className="text-foreground/70 hover:text-foreground transition-colors">
                  Términos
                </a>
              </li>
              <li>
                <a href="#" className="text-foreground/70 hover:text-foreground transition-colors">
                  Cookies
                </a>
              </li>
              <li>
                <a href="#" className="text-foreground/70 hover:text-foreground transition-colors">
                  Responsabilidad
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Copyright */}
        <div className="text-center text-sm text-foreground/60 font-mono">
          <p>© 2024 Cipher.ar. Todos los derechos reservados.</p>
          <p className="mt-2">
            Ciberseguridad seria para empresas serias.
          </p>
        </div>
      </div>
    </footer>
  );
}
