"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { useAuth, AuthProvider } from "@/components/auth-context"
import { Crosshair, Siren, LayoutDashboard, LogOut, Menu, X } from "lucide-react"

const sidebarLinks = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/attack-surface", label: "Attack Surface", icon: Crosshair },
  { href: "/dashboard/phishing", label: "Phishing", icon: Siren },
]

function DashboardShell({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth()
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login")
    }
  }, [user, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <span className="font-mono text-sm text-muted-foreground">Cargando...</span>
      </div>
    )
  }

  if (!user) return null

  return (
    <div className="min-h-screen bg-background">
      <nav className="fixed top-0 left-0 right-0 h-16 border-b border-border bg-background z-50 flex items-center px-4">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="md:hidden mr-4 text-muted-foreground hover:text-primary border border-border p-2"
        >
          {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
        </button>

        <Link href="/dashboard" className="flex items-center gap-0 font-mono text-lg font-bold tracking-widest">
          <span className="text-foreground">AU</span>
          <span className="text-primary">K</span>
          <span className="text-foreground">ALABS</span>
          <span className="text-primary text-xs ml-1 opacity-70 font-normal">_</span>
        </Link>

        <div className="ml-auto flex items-center gap-4">
          <span className="font-mono text-xs text-muted-foreground hidden sm:block">
            {user.email}
          </span>
          <button
            onClick={logout}
            className="flex items-center gap-2 font-mono text-xs text-muted-foreground hover:text-destructive border border-border px-3 py-2 transition-colors"
          >
            <LogOut size={14} />
            Salir
          </button>
        </div>
      </nav>

      <aside
        className={`fixed top-16 left-0 bottom-0 w-64 border-r border-border bg-card z-40 transform transition-transform ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } md:translate-x-0`}
      >
        <div className="p-4 space-y-1">
          {sidebarLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setSidebarOpen(false)}
              className="flex items-center gap-3 px-4 py-3 font-mono text-sm text-muted-foreground hover:text-primary hover:bg-surface-3 transition-colors"
            >
              <link.icon size={16} className="text-primary" />
              {link.label}
            </Link>
          ))}
        </div>
      </aside>

      <main className="md:ml-64 pt-16">
        <div className="p-6 sm:p-8">{children}</div>
      </main>
    </div>
  )
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <DashboardShell>{children}</DashboardShell>
    </AuthProvider>
  )
}
