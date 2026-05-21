'use client';

import { useState } from 'react';
import { Mail } from 'lucide-react';

export function NewsletterSection() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email) {
      setStatus('Suscripción registrada');
      setEmail('');
      setTimeout(() => setStatus(''), 3000);
    }
  };

  return (
    <section className="px-4 sm:px-6 lg:px-8 py-16 bg-background border-b border-foreground">
      <div className="max-w-4xl mx-auto">
        <div className="border border-foreground p-12 bg-background">
          <div className="flex items-center gap-3 mb-6">
            <Mail className="w-8 h-8 text-foreground" />
            <h3 className="text-2xl font-bold text-foreground font-mono">ALERTAS DE SEGURIDAD</h3>
          </div>

          <p className="text-foreground/70 mb-6 font-mono">
            Suscríbete para recibir alertas mensuales sobre nuevas amenazas, vulnerabilidades críticas y mejores prácticas de seguridad.
          </p>

          <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
            <input
              type="email"
              placeholder="tu@empresa.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="flex-1 px-4 py-3 bg-background border border-foreground text-foreground font-mono placeholder-foreground/40 focus:outline-none focus:ring-2 focus:ring-foreground"
            />
            <button
              type="submit"
              className="px-6 py-3 bg-foreground text-background font-bold font-mono border border-foreground hover:opacity-80 transition-opacity"
            >
              SUSCRIBIR
            </button>
          </form>

          {status && <p className="text-sm text-foreground mt-4 font-mono">{status}</p>}
        </div>
      </div>
    </section>
  );
}
