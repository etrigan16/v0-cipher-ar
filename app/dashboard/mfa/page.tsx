"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Shield, ShieldOff, Terminal, Copy, Check, Eye, EyeOff } from "lucide-react"
import { useAuth } from "@/components/auth-context"
import { api } from "@/lib/api"

export default function MfaPage() {
  const { user, loading, logout } = useAuth()
  const router = useRouter()

  const [mfaEnabled, setMfaEnabled] = useState(false)
  const [secret, setSecret] = useState("")
  const [provisioningUri, setProvisioningUri] = useState("")
  const [verifyCode, setVerifyCode] = useState("")
  const [disablePassword, setDisablePassword] = useState("")
  const [showDisablePassword, setShowDisablePassword] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [busy, setBusy] = useState(false)
  const [showSetup, setShowSetup] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login")
    }
  }, [user, loading, router])

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <span className="font-mono text-sm text-muted-foreground">Cargando...</span>
      </div>
    )
  }

  async function handleSetup() {
    setError("")
    setSuccess("")
    setBusy(true)
    try {
      const res = await api.auth.mfa.setup()
      setSecret(res.secret)
      setProvisioningUri(res.uri)
      setShowSetup(true)
      setMfaEnabled(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al generar código")
    } finally {
      setBusy(false)
    }
  }

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setSuccess("")
    setBusy(true)
    try {
      await api.auth.mfa.verify(verifyCode)
      setMfaEnabled(true)
      setShowSetup(false)
      setVerifyCode("")
      setSuccess("MFA activado correctamente")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Código inválido")
    } finally {
      setBusy(false)
    }
  }

  async function handleDisable(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setSuccess("")
    setBusy(true)
    try {
      await api.auth.mfa.disable(disablePassword)
      setMfaEnabled(false)
      setSecret("")
      setProvisioningUri("")
      setDisablePassword("")
      setSuccess("MFA desactivado correctamente")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al desactivar MFA")
    } finally {
      setBusy(false)
    }
  }

  function handleCopySecret() {
    navigator.clipboard.writeText(secret)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-8">
        <h1 className="font-mono text-2xl font-bold text-foreground">Autenticación MFA</h1>
        <p className="font-mono text-xs text-muted-foreground mt-2">
          {mfaEnabled
            ? "La autenticación de dos factores está activa"
            : "Agregá una capa extra de seguridad a tu cuenta"}
        </p>
      </div>

      {error && (
        <div className="border border-destructive bg-destructive/10 px-4 py-3 mb-6">
          <p className="font-mono text-xs text-destructive">{error}</p>
        </div>
      )}

      {success && (
        <div className="border border-emerald-500 bg-emerald-500/10 px-4 py-3 mb-6">
          <p className="font-mono text-xs text-emerald-500">{success}</p>
        </div>
      )}

      {/* Status card */}
      <div className="border border-border bg-card p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {mfaEnabled ? (
              <Shield size={24} className="text-emerald-500" />
            ) : (
              <ShieldOff size={24} className="text-muted-foreground" />
            )}
            <div>
              <p className="font-mono text-sm text-foreground">
                {mfaEnabled ? "MFA Activado" : "MFA Desactivado"}
              </p>
              <p className="font-mono text-xs text-muted-foreground mt-1">
                {mfaEnabled
                  ? "Se requiere un código TOTP al iniciar sesión"
                  : "Solo usás contraseña para iniciar sesión"}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Setup section (only when MFA is disabled) */}
      {!mfaEnabled && !showSetup && (
        <div className="border border-border bg-card p-6">
          <button
            onClick={handleSetup}
            disabled={busy}
            className="font-mono text-sm border border-primary px-6 py-3 text-primary hover:bg-primary hover:text-background transition-colors disabled:opacity-50"
          >
            {busy ? "Generando..." : "[ Configurar MFA ]"}
          </button>
        </div>
      )}

      {/* QR + verify (after setup, before verify) */}
      {showSetup && provisioningUri && (
        <div className="border border-border bg-card p-6 mb-6 space-y-6">
          <div>
            <h2 className="font-mono text-sm text-foreground mb-4">Escaneá el código QR</h2>
            <p className="font-mono text-xs text-muted-foreground mb-4">
              Usá Google Authenticator, Authy o cualquier app compatible para escanear el código.
            </p>
            {/* QR code via Google Charts API */}
            <div className="flex justify-center mb-4">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`https://chart.googleapis.com/chart?chs=200x200&chld=M|0&cht=qr&chl=${encodeURIComponent(provisioningUri)}`}
                alt="QR Code"
                className="border border-border"
                width={200}
                height={200}
              />
            </div>

            {/* Manual secret */}
            <div className="border border-border bg-background p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs text-muted-foreground">O ingresá manualmente:</span>
                <button
                  onClick={handleCopySecret}
                  className="flex items-center gap-1 font-mono text-xs text-primary hover:underline"
                >
                  {copied ? <Check size={12} /> : <Copy size={12} />}
                  {copied ? "Copiado" : "Copiar"}
                </button>
              </div>
              <p className="font-mono text-xs text-foreground break-all select-all">{secret}</p>
            </div>
          </div>

          <form onSubmit={handleVerify} className="space-y-4">
            <div>
              <label htmlFor="verify-code" className="block font-mono text-xs text-muted-foreground mb-2">
                CÓDIGO DE VERIFICACIÓN
              </label>
              <input
                id="verify-code"
                type="text"
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                value={verifyCode}
                onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                required
                className="w-full bg-background border border-border px-4 py-3 font-mono text-sm text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none transition-colors tracking-widest"
                placeholder="000000"
              />
            </div>
            <button
              type="submit"
              disabled={busy || verifyCode.length !== 6}
              className="font-mono text-sm border border-primary px-6 py-3 text-primary hover:bg-primary hover:text-background transition-colors disabled:opacity-50"
            >
              {busy ? "Verificando..." : "[ Verificar y activar ]"}
            </button>
          </form>
        </div>
      )}

      {/* Disable section (only when MFA is enabled) */}
      {mfaEnabled && (
        <div className="border border-border bg-card p-6">
          <h2 className="font-mono text-sm text-foreground mb-4">Desactivar MFA</h2>
          <p className="font-mono text-xs text-muted-foreground mb-4">
            Ingresá tu contraseña para desactivar la autenticación de dos factores.
          </p>
          <form onSubmit={handleDisable} className="space-y-4 max-w-sm">
            <div>
              <label htmlFor="disable-password" className="block font-mono text-xs text-muted-foreground mb-2">
                CONTRASEÑA
              </label>
              <div className="relative">
                <input
                  id="disable-password"
                  type={showDisablePassword ? "text" : "password"}
                  value={disablePassword}
                  onChange={(e) => setDisablePassword(e.target.value)}
                  required
                  className="w-full bg-background border border-border px-4 py-3 pr-10 font-mono text-sm text-foreground placeholder-muted-foreground focus:border-destructive focus:outline-none transition-colors"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowDisablePassword(!showDisablePassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-destructive transition-colors"
                >
                  {showDisablePassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <button
              type="submit"
              disabled={busy || !disablePassword}
              className="font-mono text-sm border border-destructive px-6 py-3 text-destructive hover:bg-destructive hover:text-background transition-colors disabled:opacity-50"
            >
              {busy ? "Desactivando..." : "[ Desactivar MFA ]"}
            </button>
          </form>
        </div>
      )}
    </div>
  )
}
