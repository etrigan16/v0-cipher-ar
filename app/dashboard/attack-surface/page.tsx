"use client"

import { useCallback, useEffect, useState } from "react"
import { Crosshair, Loader2, Plus, Search } from "lucide-react"
import { api, type Asset, type Scan } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

export default function AttackSurfacePage() {
  const [assets, setAssets] = useState<Asset[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [domain, setDomain] = useState("")
  const [scanning, setScanning] = useState(false)
  const [scan, setScan] = useState<Scan | null>(null)
  const [scanError, setScanError] = useState<string | null>(null)

  const refreshAssets = useCallback(async () => {
    try {
      const res = await api.asm.listAssets()
      setAssets(res.assets)
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron cargar los activos")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    api.asm
      .listAssets()
      .then((res) => {
        if (!cancelled) setAssets(res.assets)
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "No se pudieron cargar los activos")
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const startScan = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = domain.trim()
    if (!trimmed) return
    setScanning(true)
    setScanError(null)
    setScan(null)
    try {
      const res = await api.asm.scanDomain(trimmed)
      setScan(res.scan)
      await refreshAssets()
    } catch (err) {
      setScanError(
        err instanceof Error ? err.message : "No se pudo iniciar el escaneo"
      )
    } finally {
      setScanning(false)
    }
  }

  const assetCount = loading ? "…" : String(assets.length)

  return (
    <div>
      <div className="mb-8">
        <h1 className="font-mono text-2xl font-bold">
          ATTACK SURFACE<span className="text-primary">_</span>
        </h1>
        <p className="font-mono text-sm text-muted-foreground mt-1">
          Monitoreo de superficie de ataque
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-px bg-border mb-8">
        <div className="bg-card p-6">
          <label htmlFor="asm-domain" className="block font-mono text-xs text-muted-foreground mb-2">
            DOMINIO A ESCANEAR
          </label>
          <form onSubmit={startScan} className="flex gap-2">
            <div className="relative flex-1">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="asm-domain"
                type="text"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                placeholder="ej: empresa.com"
                className="pl-10 font-mono text-sm"
                aria-label="Dominio a escanear"
              />
            </div>
            <Button type="submit" disabled={scanning || !domain.trim()}>
              {scanning ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
              {scanning ? "Escaneando" : "Escanear"}
            </Button>
          </form>
          {scanError && (
            <p role="alert" className="font-mono text-xs text-destructive mt-3">
              {scanError}
            </p>
          )}
          {scan && (
            <p className="font-mono text-xs text-muted-foreground mt-3">
              Escaneo de {scan.domain}: <span className="text-primary">{scan.status}</span>
            </p>
          )}
        </div>

        <div className="bg-card p-6">
          <span className="font-mono text-xs text-muted-foreground">ACTIVOS MONITOREADOS</span>
          <div className="font-mono text-4xl font-bold mt-2">{assetCount}</div>
        </div>
      </div>

      {error && (
        <div role="alert" className="border border-destructive bg-card p-4 mb-6">
          <p className="font-mono text-sm text-destructive">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="border border-border bg-card p-12 text-center">
          <Loader2 className="mx-auto text-primary mb-4 animate-spin" size={32} />
          <p className="font-mono text-sm text-muted-foreground">Cargando activos…</p>
        </div>
      ) : assets.length === 0 ? (
        <div className="border border-border bg-card p-12 text-center">
          <Crosshair className="mx-auto text-primary mb-4" size={32} />
          <p className="font-mono text-sm text-muted-foreground">
            Agregá un dominio para comenzar el monitoreo.
          </p>
        </div>
      ) : (
        <div className="border border-border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Subdominio</TableHead>
                <TableHead>IP</TableHead>
                <TableHead>Puerto</TableHead>
                <TableHead>Servicio</TableHead>
                <TableHead>Fingerprint</TableHead>
                <TableHead>Riesgo</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Descubierto</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {assets.map((a) => (
                <TableRow key={a.id}>
                  <TableCell className="font-mono text-xs">{a.subdomain ?? a.domain}</TableCell>
                  <TableCell className="font-mono text-xs">{a.ip ?? "—"}</TableCell>
                  <TableCell className="font-mono text-xs">{a.port ?? "—"}</TableCell>
                  <TableCell className="font-mono text-xs">{a.service ?? "—"}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {typeof a.fingerprint?.title === "string" ? a.fingerprint.title : "—"}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {a.risk_score ?? "—"}
                  </TableCell>
                  <TableCell className="font-mono text-xs">{a.status}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {a.first_seen ? new Date(a.first_seen).toLocaleDateString() : "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
