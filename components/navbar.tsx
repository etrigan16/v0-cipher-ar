'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Menu, X } from 'lucide-react';

export function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { href: '#servicios', label: 'SERVICIOS' },
    { href: '#casos', label: 'CASOS DE ESTUDIO' },
    { href: '#amenazas', label: 'AMENAZAS' },
    { href: '#riesgos', label: 'CALCULADORA' },
    { href: '#sobre', label: 'SOBRE NOSOTROS' },
    { href: '#faq', label: 'FAQ' },
    { href: '#contacto', label: 'CONTACTO' },
  ];

  return (
    <nav className="fixed top-0 w-full bg-background border-b border-foreground z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="#" className="text-foreground font-bold text-xl tracking-wider hover:opacity-70">
            CIPHER.AR
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex gap-8">
            {navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="text-foreground text-sm font-mono tracking-widest hover:opacity-70 transition-opacity"
              >
                {item.label}
              </a>
            ))}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden text-foreground border border-foreground p-2 hover:bg-foreground hover:text-background"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-foreground bg-background">
            {navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="block px-4 py-3 text-foreground text-sm font-mono border-b border-foreground hover:bg-foreground hover:text-background"
                onClick={() => setMobileMenuOpen(false)}
              >
                {item.label}
              </a>
            ))}
          </div>
        )}
      </div>
    </nav>
  );
}
