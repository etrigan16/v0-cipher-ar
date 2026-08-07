"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Terminal, Eye, EyeOff, ShieldCheck } from "lucide-react"
import { AuthProvider, useAuth } from "@/components/auth-context"

function LoginForm() {
  const { login, mfaChallenge, completeMfaChallenge, clearMfaChallenge } = useAuth()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [totpCode, setTotpCode] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      const { mfaRequired } = await login(email, password)
      if (!mfaRequired) {
        router.push("/dashboard")
      }
      // When mfaRequired is true the AuthContext surfaces the TOTP step
      // (mfaChallenge) and we stay on this page.
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión")
    } finally {
      setLoading(false)
    }
  }

  async function handleTotpSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      await completeMfaChallenge(totpCode)
      router.push("/dashboard")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Código inválido")
    } finally {
      setLoading(false)
    }
  }

  const inputClass =
    "w-full bg-background border border-border px-4 py-3 font-mono text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none transition-colors"
  const labelClass = "block font-mono text-xs text-muted-foreground mb-2"

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
              {mfaChallenge ? "$ auka auth --verify" : "$ auka auth --login"}
            </span>
          </div>

          {error && (
            <div className="border border-destructive bg-destructive/10 px-4 py-3">
              <p className="font-mono text-xs text-destructive">{error}</p>
            </div>
          )}

          {mfaChallenge ? (
            <form onSubmit={handleTotpSubmit} className="p-6 space-y-6">
              <div className="flex items-center gap-2">
                <ShieldCheck size={16} className="text-primary" />
                <p className="font-mono text-xs text-muted-foreground">
                  Ingresá el código de tu app de autenticación para {mfaChallenge.email}
                </p>
              </div>

              <div>
                <label htmlFor="totp-code" className={labelClass}>
                  CÓDIGO TOTP
                </label>
                <input
                  id="totp-code"
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  value={totpCode}
                  onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  required
                  className={`${inputClass} tracking-widest`}
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
                onClick={clearMfaChallenge}
                className="w-full font-mono text-xs text-muted-foreground hover:text-primary transition-colors"
              >
                Volver al inicio de sesión
              </button>
            </form>
          ) : (
            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              <div>
                <label htmlFor="email" className={labelClass}>
                  EMAIL
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className={inputClass}
                  placeholder="user@empresa.com"
                />
              </div>

              <div>
                <label htmlFor="password" className={labelClass}>
                  PASSWORD
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className={`${inputClass} pr-10`}
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary transition-colors"
                    aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
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
          )}
        </div>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <AuthProvider>
      <LoginForm />
    </AuthProvider>
  )
}
