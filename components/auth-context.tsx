"use client"

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react"
import { api } from "@/lib/api"

type User = {
  id: string
  email: string
  name: string
}

export type MfaChallenge = {
  partialToken: string
  email: string
}

type AuthContextType = {
  user: User | null
  token: string | null
  loading: boolean
  mfaChallenge: MfaChallenge | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string) => Promise<void>
  logout: () => void
  completeMfaChallenge: (code: string) => Promise<void>
  clearMfaChallenge: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [mfaChallenge, setMfaChallenge] = useState<MfaChallenge | null>(null)

  useEffect(() => {
    const stored = localStorage.getItem("token")
    if (stored) {
      setToken(stored)
      api.auth.me()
        .then(setUser)
        .catch(() => {
          localStorage.removeItem("token")
          setToken(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.auth.login(email, password)

    if ("mfa_required" in res && res.mfa_required) {
      setMfaChallenge({ partialToken: res.partial_token, email })
      return
    }

    localStorage.setItem("token", (res as { access_token: string }).access_token)
    setToken((res as { access_token: string }).access_token)
    const me = await api.auth.me()
    setUser(me)
  }, [])

  const completeMfaChallenge = useCallback(async (code: string) => {
    if (!mfaChallenge) throw new Error("No MFA challenge active")

    const res = await api.auth.mfa.challenge(mfaChallenge.partialToken, code)
    localStorage.setItem("token", res.access_token)
    setToken(res.access_token)
    setMfaChallenge(null)
    const me = await api.auth.me()
    setUser(me)
  }, [mfaChallenge])

  const clearMfaChallenge = useCallback(() => {
    setMfaChallenge(null)
  }, [])

  const register = useCallback(async (email: string, password: string, name: string) => {
    await api.auth.register(email, password, name)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem("token")
    setToken(null)
    setUser(null)
    setMfaChallenge(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, loading, mfaChallenge, login, register, logout, completeMfaChallenge, clearMfaChallenge }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
