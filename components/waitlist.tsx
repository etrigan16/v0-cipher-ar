"use client"

import { useState } from "react"
import { Send, Loader2 } from "lucide-react"
import { api } from "@/lib/api"

// Simple email regex for client-side validation before submit
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function WaitlistSection() {
  const [email, setEmail] = useState("")
  const [company, setCompany] = useState("")
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle")
  const [errorMessage, setErrorMessage] = useState("")

  const inputClass =
    "w-full px-4 py-3 bg-[#000000] border border-[#1a1a1a] text-foreground font-mono text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:border-primary focus-visible:ring-0 rounded-none transition-colors"

  const isValidEmail = EMAIL_RE.test(email)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage("")

    // Client-side validation
    if (!email.trim()) {
      setStatus("error")
      setErrorMessage("Email is required")
      return
    }
    if (!isValidEmail) {
      setStatus("error")
      setErrorMessage("Invalid email format")
      return
    }

    setStatus("loading")

    try {
      await api.waitlist.submit(email.trim(), company.trim() || undefined)
      setStatus("success")
      setEmail("")
      setCompany("")
    } catch (err) {
      setStatus("error")
      setErrorMessage(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  return (
    <section id="waitlist" className="px-4 sm:px-6 lg:px-8 py-20 bg-surface-2">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-12 text-center">
          <span className="font-mono text-xs text-primary tracking-[0.2em]">
            WAITLIST
          </span>
          <h2 className="font-mono text-3xl sm:text-4xl font-bold mt-4 mb-4">
            EARLY ACCESS<span className="text-primary">_</span>
          </h2>
          <p className="text-muted-foreground font-mono text-sm leading-relaxed">
            Be the first to know about Aukalabs launches, features, and security insights.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <label
                htmlFor="waitlist-email"
                className="font-mono text-xs text-muted-foreground uppercase tracking-widest"
              >
                Email <span className="text-primary">*</span>
              </label>
              <input
                id="waitlist-email"
                type="email"
                placeholder="user@example.com"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                  if (status === "error") setStatus("idle")
                }}
                required
                className={inputClass}
              />
            </div>
            <div className="flex flex-col gap-2">
              <label
                htmlFor="waitlist-company"
                className="font-mono text-xs text-muted-foreground uppercase tracking-widest"
              >
                Company
              </label>
              <input
                id="waitlist-company"
                type="text"
                placeholder="Acme Corp"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className={inputClass}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={status === "loading"}
            className="w-full px-6 py-4 bg-primary text-primary-foreground font-mono text-sm font-bold tracking-widest uppercase hover:opacity-90 active:opacity-80 transition-opacity flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {status === "loading" ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                JOINING...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                JOIN WAITLIST
              </>
            )}
          </button>
        </form>

        {/* Status messages */}
        {status === "success" && (
          <p className="mt-4 text-sm text-primary font-mono text-center border border-primary px-4 py-3">
            {"// You're on the list! We'll keep you posted."}
          </p>
        )}
        {status === "error" && (
          <p className="mt-4 text-sm text-destructive font-mono text-center border border-destructive/50 px-4 py-3">
            {"// "}{errorMessage}
          </p>
        )}
      </div>
    </section>
  )
}
