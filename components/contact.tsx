"use client"

import { useState } from "react"
import { Mail, Send } from "lucide-react"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const challenges = [
  {
    value: "infra-pyme",
    label: "Necesito auditar o segmentar la red/WiFi de mi oficina (Infraestructura PyME)",
  },
  {
    value: "mvp-software",
    label: "Quiero construir un MVP o software con seguridad nativa desde cero (Next.js/Nest.js)",
  },
  {
    value: "firewall-caidas",
    label: "Tengo problemas de caídas o configuraciones de Firewalls/Servidores",
  },
  {
    value: "audit-express",
    label: "Quiero solicitar una evaluación técnica rápida (Audit Express de 48-72hs)",
  },
  {
    value: "otro",
    label: "Otro desafío técnico / Consultoría general",
  },
]

export function ContactSection() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    company: "",
    challenge: "",
    description: "",
  })
  const [status, setStatus] = useState("")

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleChallengeChange = (value: string) => {
    setFormData({ ...formData, challenge: value })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (formData.name && formData.email && formData.challenge && formData.description) {
      setStatus("PROCESANDO INFORMACIÓN... ESTABLECIENDO CONEXIÓN CON EL SERVIDOR.")

      try {
        // Hacemos el disparo de red a nuestra Serverless Function
        const response = await fetch("/api/send", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            nombre: formData.name,
            email: formData.email,
            empresa: formData.company || "No especificada",
            desafio: formData.challenge,
            descripcion: formData.description,
          }),
        })

        if (response.ok) {
          setStatus("SOLICITUD RECIBIDA CON ÉXITO. REVISANDO PARÁMETROS EN MENOS DE 24 HORAS.")
          // Limpiamos el formulario una vez enviado con éxito
          setFormData({ name: "", email: "", company: "", challenge: "", description: "" })
        } else {
          setStatus("ERROR CRÍTICO: El servidor rechazó la solicitud de envío.")
        }
      } catch (error) {
        console.error("Fallo de red:", error)
        setStatus("FALLO INTERNO DE CONECTIVIDAD: Intenta de nuevo más tarde.")
      }

      // Quitamos el cartel de estado después de 6 segundos
      setTimeout(() => setStatus(""), 6000)
    }
  }

  const inputClass =
    "w-full px-4 py-3 bg-[#000000] border border-[#1a1a1a] text-foreground font-mono text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:border-primary focus-visible:ring-0 rounded-none transition-colors"

  return (
    <section id="contacto" className="px-4 sm:px-6 lg:px-8 py-20 bg-surface-1">
      <div className="max-w-2xl mx-auto">

        {/* Header */}
        <div className="mb-12">
          <p className="font-mono text-xs text-primary uppercase tracking-widest mb-3">
            // CALIFICACIÓN DE PROYECTO
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4 leading-tight">
            Cuéntanos tu desafío.<br />
            <span className="text-primary">Lo analizamos en 24hs.</span>
          </h2>
          <p className="text-muted-foreground font-sans text-sm leading-relaxed">
            Completa el formulario y recibirás una evaluación inicial sin costo. Sin spam, sin presión.
          </p>
        </div>

        {/* Email line */}
        <div className="flex items-center gap-2 mb-10 pb-8 border-b border-[#1a1a1a]">
          <Mail className="w-4 h-4 text-muted-foreground" />
          <a
            href="mailto:contact@aukalabs.com"
            className="font-mono text-sm text-muted-foreground hover:text-primary transition-colors"
          >
            contact@aukalabs.com
          </a>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">

          {/* Row 1: Nombre + Email */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="name" className="font-mono text-xs text-muted-foreground uppercase tracking-widest">
                Nombre Completo <span className="text-primary">*</span>
              </Label>
              <Input
                id="name"
                name="name"
                type="text"
                placeholder="Juan García"
                value={formData.name}
                onChange={handleChange}
                required
                className={inputClass}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="email" className="font-mono text-xs text-muted-foreground uppercase tracking-widest">
                Email Corporativo <span className="text-primary">*</span>
              </Label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="juan@empresa.com"
                value={formData.email}
                onChange={handleChange}
                required
                className={inputClass}
              />
            </div>
          </div>

          {/* Row 2: Empresa */}
          <div className="flex flex-col gap-2">
            <Label htmlFor="company" className="font-mono text-xs text-muted-foreground uppercase tracking-widest">
              Nombre de la Empresa / Startup
            </Label>
            <Input
              id="company"
              name="company"
              type="text"
              placeholder="Acme Corp / Mi Startup SRL"
              value={formData.company}
              onChange={handleChange}
              className={inputClass}
            />
          </div>

          {/* Row 3: Desafío técnico */}
          <div className="flex flex-col gap-2">
            <Label htmlFor="challenge" className="font-mono text-xs text-muted-foreground uppercase tracking-widest">
              Principal Desafío Técnico <span className="text-primary">*</span>
            </Label>
            <Select value={formData.challenge} onValueChange={handleChallengeChange} required>
              <SelectTrigger
                id="challenge"
                className="w-full px-4 py-3 bg-[#000000] border border-[#1a1a1a] text-foreground font-mono text-sm rounded-none focus:ring-0 focus:border-primary hover:border-primary transition-colors data-[placeholder]:text-muted-foreground h-auto"
              >
                <SelectValue placeholder="Selecciona tu desafío..." />
              </SelectTrigger>
              <SelectContent className="bg-[#0a0a0a] border border-[#1a1a1a] rounded-none font-mono text-sm">
                {challenges.map((c) => (
                  <SelectItem
                    key={c.value}
                    value={c.value}
                    className="text-foreground focus:bg-primary focus:text-primary-foreground rounded-none cursor-pointer py-3"
                  >
                    {c.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Row 4: Descripción */}
          <div className="flex flex-col gap-2">
            <Label htmlFor="description" className="font-mono text-xs text-muted-foreground uppercase tracking-widest">
              Describe tu infraestructura o problema <span className="text-primary">*</span>
            </Label>
            <Textarea
              id="description"
              name="description"
              placeholder="Ej: Tenemos una red corporativa con 20 equipos, sin VLANs, y necesitamos separar el tráfico de empleados del de clientes..."
              value={formData.description}
              onChange={handleChange}
              required
              rows={5}
              className={`${inputClass} resize-none`}
            />
          </div>

          {/* Submit */}
          <button
            type="submit"
            className="w-full px-6 py-4 bg-primary text-primary-foreground font-mono text-sm font-bold tracking-widest uppercase hover:opacity-90 active:opacity-80 transition-opacity flex items-center justify-center gap-3"
          >
            <Send className="w-4 h-4" />
            ENVIAR CALIFICACIÓN DE PROYECTO
          </button>

          {status && (
            <p className="text-sm text-primary font-mono text-center border border-primary px-4 py-3">
              // {status}
            </p>
          )}

        </form>
      </div>
    </section>
  )
}
