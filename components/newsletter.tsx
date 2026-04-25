"use client"

import { useState } from "react"
import { Mail, CheckCircle, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"

export function NewsletterSection() {
  const [email, setEmail] = useState("")
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email) return
    
    setStatus("loading")
    
    // Simular envio - aqui se conectaria con el servicio de newsletter
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    setStatus("success")
    setEmail("")
  }

  return (
    <section className="px-6 lg:px-12 py-20 border-t border-border">
      <div className="max-w-2xl mx-auto text-center">
        <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-6">
          <Mail className="w-7 h-7 text-primary" />
        </div>
        
        <h2 className="text-2xl md:text-3xl font-bold text-foreground mb-4 text-balance">
          Mantente informado sobre amenazas de seguridad
        </h2>
        <p className="text-muted-foreground mb-8">
          Recibe alertas de vulnerabilidades, consejos de seguridad y actualizaciones directamente en tu correo.
        </p>

        {status === "success" ? (
          <div className="flex items-center justify-center gap-2 text-green-400 bg-green-500/10 border border-green-500/30 rounded-lg p-4">
            <CheckCircle className="w-5 h-5" />
            <span>Gracias por suscribirte. Pronto recibiras nuestras actualizaciones.</span>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="tu@email.com"
              required
              className="flex-1 px-4 py-3 rounded-lg bg-card border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            />
            <Button 
              type="submit" 
              disabled={status === "loading"}
              className="bg-primary text-primary-foreground hover:bg-primary/90 px-6"
            >
              {status === "loading" ? "Enviando..." : "Suscribirse"}
            </Button>
          </form>
        )}

        {status === "error" && (
          <div className="flex items-center justify-center gap-2 text-red-400 mt-4">
            <AlertCircle className="w-5 h-5" />
            <span>Hubo un error. Por favor, intenta nuevamente.</span>
          </div>
        )}

        <p className="text-xs text-muted-foreground mt-4">
          No spam. Puedes darte de baja en cualquier momento.
        </p>
      </div>
    </section>
  )
}
