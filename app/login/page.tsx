"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Terminal, Eye, EyeOff } from "lucide-react"
import { api } from "@/lib/api"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      const res = await api.auth.login(email, password)
      localStorage.setItem("token", res.access_token)
      router.push("/dashboard")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-10">
          <Link href="/" className="inline-flex items-center gap-0 font-mono text-2xl font-bold tracking-widest">
            <span className="text-foreground">AU</span>
            <span className="text-primary">K</span>
            <span className="text-foreground">ALABS</span>
            <span className="text-primary text-xs ml-1 opacity-70 font-normal">_</span>
          </Link>
        </div>

        <div className="border border-border bg-card">
          <div className="border-b border-border px-6 py-4 flex items-center gap-2">
            <Terminal size={16} className="text-primary" />
            <span className="font-mono text-xs text-muted-foreground">
              $ auka auth --login
            </span>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {error && (
              <div className="border border-destructive bg-destructive/10 px-4 py-3">
                <p className="font-mono text-xs text-destructive">{error}</p>
              </div>
            )}

            <div>
              <label htmlFor="email" className="block font-mono text-xs text-muted-foreground mb-2">
                EMAIL
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-background border border-border px-4 py-3 font-mono text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none transition-colors"
                placeholder="user@empresa.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block font-mono text-xs text-muted-foreground mb-2">
                PASSWORD
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full bg-background border border-border px-4 py-3 pr-10 font-mono text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none transition-colors"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary transition-colors"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full font-mono text-sm border border-primary px-6 py-3 text-primary hover:bg-primary hover:text-background transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Autenticando..." : "[ Iniciar sesión ]"}
            </button>

            <p className="text-center font-mono text-xs text-muted-foreground">
              ¿No tenés cuenta?{" "}
              <Link href="/register" className="text-primary hover:underline">
                Registrate
              </Link>
            </p>
          </form>
        </div>
      </div>
    </div>
  )
}
