'use client';

import { useState } from 'react';
import { Mail, Phone, MapPin, Send } from 'lucide-react';

export function ContactSection() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    message: '',
  });
  const [status, setStatus] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.name && formData.email && formData.message) {
      setStatus('Mensaje enviado. Te contactaremos pronto.');
      setFormData({ name: '', email: '', company: '', message: '' });
      setTimeout(() => setStatus(''), 4000);
    }
  };

  return (
    <section id="contacto" className="px-4 sm:px-6 lg:px-8 py-20 bg-background border-b border-foreground">
      <div className="max-w-7xl mx-auto">
        <h2 className="text-4xl sm:text-5xl font-bold text-foreground font-mono mb-4">CONTACTO</h2>
        <div className="w-16 h-1 bg-foreground mb-12"></div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Contact Info */}
          <div>
            <h3 className="text-2xl font-bold text-foreground font-mono mb-8">INFORMACIÓN DE CONTACTO</h3>

            <div className="space-y-6">
              <div className="flex items-start gap-4">
                <Mail className="w-6 h-6 text-foreground flex-shrink-0 mt-1" />
                <div>
                  <p className="font-mono font-bold text-foreground">EMAIL</p>
                  <a
                    href="mailto:contacto@cipher.ar"
                    className="text-foreground/70 hover:text-foreground transition-colors"
                  >
                    contacto@cipher.ar
                  </a>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <Phone className="w-6 h-6 text-foreground flex-shrink-0 mt-1" />
                <div>
                  <p className="font-mono font-bold text-foreground">TELÉFONO</p>
                  <a
                    href="tel:+5491123456789"
                    className="text-foreground/70 hover:text-foreground transition-colors"
                  >
                    +54 9 11 2345 6789
                  </a>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <MapPin className="w-6 h-6 text-foreground flex-shrink-0 mt-1" />
                <div>
                  <p className="font-mono font-bold text-foreground">UBICACIÓN</p>
                  <p className="text-foreground/70">Buenos Aires, Argentina</p>
                </div>
              </div>
            </div>

            <div className="mt-12 pt-12 border-t border-foreground">
              <p className="text-sm text-foreground/60 font-mono">
                Disponibilidad: Lunes a Viernes, 9:00 - 18:00 (ART)
                <br />
                Emergencias de seguridad: 24/7
              </p>
            </div>
          </div>

          {/* Contact Form */}
          <div>
            <h3 className="text-2xl font-bold text-foreground font-mono mb-8">SOLICITA UNA CONSULTA</h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              <input
                type="text"
                name="name"
                placeholder="Tu nombre"
                value={formData.name}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 bg-background border border-foreground text-foreground font-mono placeholder-foreground/40 focus:outline-none focus:ring-2 focus:ring-foreground"
              />
              <input
                type="email"
                name="email"
                placeholder="tu@empresa.com"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 bg-background border border-foreground text-foreground font-mono placeholder-foreground/40 focus:outline-none focus:ring-2 focus:ring-foreground"
              />
              <input
                type="text"
                name="company"
                placeholder="Tu empresa (opcional)"
                value={formData.company}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-background border border-foreground text-foreground font-mono placeholder-foreground/40 focus:outline-none focus:ring-2 focus:ring-foreground"
              />
              <textarea
                name="message"
                placeholder="Cuéntanos sobre tu necesidad de seguridad..."
                value={formData.message}
                onChange={handleChange}
                required
                rows={5}
                className="w-full px-4 py-3 bg-background border border-foreground text-foreground font-mono placeholder-foreground/40 focus:outline-none focus:ring-2 focus:ring-foreground resize-none"
              />

              <button
                type="submit"
                className="w-full px-6 py-3 bg-foreground text-background font-bold font-mono border border-foreground hover:opacity-80 transition-opacity flex items-center justify-center gap-2"
              >
                <Send size={20} />
                ENVIAR CONSULTA
              </button>

              {status && <p className="text-sm text-foreground font-mono text-center">{status}</p>}
            </form>
          </div>
        </div>
      </div>
    </section>
  );
}
