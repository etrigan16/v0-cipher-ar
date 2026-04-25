"use client"

import { useState } from "react"
import { Shield, Menu, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"

const navLinks = [
  { href: "#servicios", label: "Servicios" },
  { href: "#casos", label: "Casos de Estudio" },
  { href: "#amenazas", label: "Amenazas" },
  { href: "#nosotros", label: "Nosotros" },
  { href: "#faq", label: "FAQ" },
  { href: "#contacto", label: "Contacto" },
]

export function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <nav className="border-b border-border bg-background/80 backdrop-blur-md sticky top-0 z-50">
      <div className="flex items-center justify-between px-6 lg:px-12 py-4 max-w-7xl mx-auto">
        <Link href="/" className="flex items-center gap-2">
          <Shield className="w-7 h-7 text-primary" />
          <span className="font-semibold text-foreground text-lg">Guillermo A. Fernandez</span>
        </Link>
        
        <div className="hidden lg:flex items-center gap-8 text-sm text-muted-foreground">
          {navLinks.map((link) => (
            <Link 
              key={link.href}
              href={link.href} 
              className="hover:text-foreground transition-colors"
            >
              {link.label}
            </Link>
          ))}
        </div>
        
        <div className="flex items-center gap-3">
          <Button 
            asChild
            className="hidden sm:inline-flex bg-primary text-primary-foreground hover:bg-primary/90"
          >
            <Link href="#contacto">Consulta Gratis</Link>
          </Button>
          <Button 
            variant="ghost" 
            size="icon" 
            className="lg:hidden text-foreground"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </Button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-border bg-background">
          <div className="px-6 py-4 flex flex-col gap-4">
            {navLinks.map((link) => (
              <Link 
                key={link.href}
                href={link.href} 
                className="text-muted-foreground hover:text-foreground transition-colors py-2"
                onClick={() => setMobileMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            <Button 
              asChild
              className="mt-2 bg-primary text-primary-foreground hover:bg-primary/90 w-full"
            >
              <Link href="#contacto" onClick={() => setMobileMenuOpen(false)}>
                Consulta Gratis
              </Link>
            </Button>
          </div>
        </div>
      )}
    </nav>
  )
}
