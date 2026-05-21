"use client"

import { useState } from "react"
import { Mail, Send } from "lucide-react"

export function ContactSection() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    company: "",
    message: "",
  })
  const [status, setStatus] = useState("")

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (formData.name && formData.email && formData.message) {
      setStatus("Mensaje enviado. Te contactaremos pronto.")
      setFormData({ name: "", email: "", company: "", message: "" })
      setTimeout(() => setStatus(""), 4000)
    }
  }

  return (
    <section id="contacto" className="px-4 sm:px-6 lg:px-8 py-20 bg-card border-b border-border">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <p className="font-mono text-sm text-primary mb-2">// CONTACTO</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
            Hablemos de tu seguridad
          </h2>
          <p className="text-muted-foreground">
            Cuéntanos sobre tu infraestructura y necesidades. Respuesta en menos de 24 horas.
          </p>
        </div>

        {/* Contact Info */}
        <div className="flex items-center justify-center gap-2 mb-8 text-muted-foreground">
          <Mail className="w-4 h-4" />
          <a href="mailto:contact@cipher.ar" className="font-mono text-sm hover:text-primary transition-colors">
            contact@cipher.ar
          </a>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <input
              type="text"
              name="name"
              placeholder="Nombre"
              value={formData.name}
              onChange={handleChange}
              required
              className="w-full px-4 py-3 bg-background border border-border text-foreground font-mono text-sm placeholder-muted-foreground focus:outline-none focus:border-primary transition-colors"
            />
            <input
              type="email"
              name="email"
              placeholder="email@empresa.com"
              value={formData.email}
              onChange={handleChange}
              required
              className="w-full px-4 py-3 bg-background border border-border text-foreground font-mono text-sm placeholder-muted-foreground focus:outline-none focus:border-primary transition-colors"
            />
          </div>
          <input
            type="text"
            name="company"
            placeholder="Empresa (opcional)"
            value={formData.company}
            onChange={handleChange}
            className="w-full px-4 py-3 bg-background border border-border text-foreground font-mono text-sm placeholder-muted-foreground focus:outline-none focus:border-primary transition-colors"
          />
          <textarea
            name="message"
            placeholder="Describe tu necesidad de seguridad..."
            value={formData.message}
            onChange={handleChange}
            required
            rows={5}
            className="w-full px-4 py-3 bg-background border border-border text-foreground font-mono text-sm placeholder-muted-foreground focus:outline-none focus:border-primary transition-colors resize-none"
          />

          <button
            type="submit"
            className="w-full px-6 py-3 bg-primary text-primary-foreground font-mono text-sm font-medium hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
          >
            <Send className="w-4 h-4" />
            ENVIAR MENSAJE
          </button>

          {status && (
            <p className="text-sm text-primary font-mono text-center">{status}</p>
          )}
        </form>
      </div>
    </section>
  )
}
