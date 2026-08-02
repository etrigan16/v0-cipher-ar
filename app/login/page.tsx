"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Terminal, Eye, EyeOff, ScanLine } from "lucide-react"
import { useAuth } from "@/components/auth-context"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [totpCode, setTotpCode] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const { login, mfaChallenge, completeMfaChallenge, clearMfaChallenge } = useAuth()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      await login(email, password)
      if (!mfaChallenge) {
        router.push("/dashboard")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión")
    } finally {
      setLoading(false)
    }
  }

  async function handleMfaSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      await completeMfaChallenge(totpCode)
      router.push("/dashboard")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Código inválido")
      setTotpCode("")
    } finally {
      setLoading(false)
    }
  }

  function handleBack() {
    clearMfaChallenge()
    setError("")
  }

  const isMfaStep = !!mfaChallenge

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
              $ {isMfaStep ? "auka auth --mfa-challenge" : "auka auth --login"}
            </span>
          </div>

          {!isMfaStep ? (
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
          ) : (
            <form onSubmit={handleMfaSubmit} className="p-6 space-y-6">
              <div className="flex items-center gap-2 px-4 py-3 bg-primary/5 border border-primary/20">
                <ScanLine size={16} className="text-primary" />
                <p className="font-mono text-xs text-muted-foreground">
                  Ingresá el código de 6 dígitos de tu app de autenticación
                </p>
              </div>

              {error && (
                <div className="border border-destructive bg-destructive/10 px-4 py-3">
                  <p className="font-mono text-xs text-destructive">{error}</p>
                </div>
              )}

              <div>
                <label htmlFor="totp" className="block font-mono text-xs text-muted-foreground mb-2">
                  CÓDIGO TOTP
                </label>
                <input
                  id="totp"
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  value={totpCode}
                  onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  required
                  autoFocus
                  className="w-full bg-background border border-border px-4 py-3 font-mono text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none transition-colors tracking-widest text-center text-2xl"
                  placeholder="000000"
                />
              </div>

              <button
                type="submit"
                disabled={loading || totpCode.length !== 6}
                className="w-full font-mono text-sm border border-primary px-6 py-3 text-primary hover:bg-primary hover:text-background transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Verificando..." : "[ Verificar código ]"}
              </button>

              <button
                type="button"
                onClick={handleBack}
                className="w-full font-mono text-xs text-muted-foreground hover:text-primary transition-colors"
              >
                Volver al inicio de sesión
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
