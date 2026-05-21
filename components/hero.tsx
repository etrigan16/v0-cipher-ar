"use client"

import { useEffect, useState } from "react"
import { ArrowRight, Terminal } from "lucide-react"

const terminalLines = [
  { text: "$ cipher --audit --target=infrastructure", delay: 0 },
  { text: "[SCAN] Analyzing network topology...", delay: 800 },
  { text: "[SCAN] Checking firewall rules...", delay: 1600 },
  { text: "[VULN] Found 3 critical vulnerabilities", delay: 2400 },
  { text: "[FIX] Generating remediation plan...", delay: 3200 },
  { text: "[OK] Security posture: HARDENED", delay: 4000 },
]

function TerminalSimulator() {
  const [visibleLines, setVisibleLines] = useState<number>(0)
  const [cursorVisible, setCursorVisible] = useState(true)

  useEffect(() => {
    const lineTimers = terminalLines.map((line, index) =>
      setTimeout(() => setVisibleLines(index + 1), line.delay)
    )

    const cursorInterval = setInterval(() => {
      setCursorVisible((v) => !v)
    }, 500)

    return () => {
      lineTimers.forEach(clearTimeout)
      clearInterval(cursorInterval)
    }
  }, [])

  return (
    <div className="border border-border bg-card p-4 font-mono text-sm">
      <div className="flex items-center gap-2 border-b border-border pb-2 mb-3">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 bg-destructive"></div>
          <div className="w-3 h-3 bg-primary/50"></div>
          <div className="w-3 h-3 bg-primary"></div>
        </div>
        <span className="text-muted-foreground text-xs">cipher@secure:~</span>
      </div>
      <div className="space-y-1 min-h-[180px]">
        {terminalLines.slice(0, visibleLines).map((line, index) => (
          <div key={index} className={`${line.text.includes("[VULN]") ? "text-destructive" : line.text.includes("[OK]") ? "text-primary" : "text-foreground"}`}>
            {line.text}
          </div>
        ))}
        {visibleLines < terminalLines.length && (
          <span className={`${cursorVisible ? "opacity-100" : "opacity-0"} text-primary`}>_</span>
        )}
      </div>
    </div>
  )
}

export function HeroSection() {
  return (
    <section className="pt-24 pb-16 px-4 sm:px-6 lg:px-8 bg-background border-b border-border">
      <div className="max-w-7xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left: Copy */}
          <div>
            <p className="font-mono text-sm text-primary mb-4 tracking-wider">
              // CIPHER.AR — CONSULTORÍA TÁCTICA
            </p>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground leading-tight mb-6 text-balance">
              Diseñamos sistemas que no pueden permitirse fallar.
            </h1>
            <p className="text-lg text-muted-foreground mb-8 leading-relaxed max-w-xl">
              Infraestructura robusta. Software blindado. Consultoría táctica en ciberseguridad y redes para empresas que toman en serio su protección digital.
            </p>
            
            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4">
              <a
                href="#audit-express"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-primary text-primary-foreground font-mono text-sm font-medium hover:opacity-90 transition-opacity"
              >
                AUDIT EXPRESS
                <ArrowRight size={18} />
              </a>
              <a
                href="#soluciones"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-border text-foreground font-mono text-sm font-medium hover:border-primary hover:text-primary transition-colors"
              >
                VER SOLUCIONES
              </a>
            </div>
          </div>

          {/* Right: Terminal */}
          <div className="lg:pl-8">
            <TerminalSimulator />
          </div>
        </div>
      </div>
    </section>
  )
}

export function TrustedBySection() {
  return (
    <section className="px-4 sm:px-6 lg:px-8 py-12 border-b border-border bg-background">
      <div className="max-w-7xl mx-auto">
        <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-6 text-center">
          // INFRAESTRUCTURA Y DESARROLLO SEGURO PARA:
        </p>
        <div className="flex flex-wrap justify-center items-center gap-6 md:gap-12">
          {["Startups & MVPs", "Infraestructura PyME", "Redes Distribuidas"].map((segment, i) => (
            <div key={i} className="font-mono text-sm text-muted-foreground hover:text-primary transition-colors">
              [{segment}]
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
