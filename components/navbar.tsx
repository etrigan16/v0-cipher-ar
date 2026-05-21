"use client"

import { useState } from "react"
import Link from "next/link"
import { Menu, X } from "lucide-react"

const navItems = [
  { href: "#soluciones", label: "Soluciones" },
  { href: "#intelligence", label: "Intelligence" },
  { href: "#audit-express", label: "Audit Express" },
]

export function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <nav className="fixed top-0 w-full bg-background border-b border-border z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="#" className="font-mono text-xl font-bold tracking-wider">
            <span className="text-foreground">CIPHER</span>
            <span className="text-primary">.AR</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            {navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="font-mono text-sm text-muted-foreground hover:text-primary transition-colors"
              >
                [{item.label}]
              </a>
            ))}
            <a
              href="#contacto"
              className="font-mono text-sm border border-primary px-4 py-2 text-primary hover:bg-primary hover:text-background transition-colors"
            >
              [Contacto]
            </a>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden text-foreground border border-border p-2 hover:border-primary hover:text-primary transition-colors"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-border bg-background">
            {navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="block px-4 py-3 font-mono text-sm text-muted-foreground border-b border-border hover:text-primary hover:bg-card transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                [{item.label}]
              </a>
            ))}
            <a
              href="#contacto"
              className="block px-4 py-3 font-mono text-sm text-primary border-b border-border hover:bg-primary hover:text-background transition-colors"
              onClick={() => setMobileMenuOpen(false)}
            >
              [Contacto]
            </a>
          </div>
        )}
      </div>
    </nav>
  )
}
