const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

/** Build the headers shared by every request: JSON content type plus the
 * stored bearer token when present. Extra headers override the defaults and
 * never replace the Authorization header. */
function buildHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...extra,
  }
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }
  return headers
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: buildHeaders(options.headers as Record<string, string> | undefined),
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Error desconocido" }))
    throw new Error(error.detail || `HTTP ${res.status}`)
  }

  return res.json()
}

export type Asset = {
  id: string
  domain: string
  subdomain: string | null
  ip: string | null
  port: number | null
  service: string | null
  fingerprint: Record<string, unknown> | null
  status: string
  risk_score: number | null
  first_seen: string
  last_seen: string
}

export type Scan = {
  id: string
  domain: string
  status: string
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export type Finding = {
  id: string
  asset_id: string
  severity: string
  title: string
  detail: string | null
  risk_score: number | null
  risk_level: string | null
  finding_type: string | null
  remediation: string | null
  status: string
  enriched_at: string | null
  discovered_at: string
}

export type SeverityCounts = {
  info: number
  low: number
  medium: number
  high: number
  critical: number
}

export type RiskSummary = {
  severity_counts: SeverityCounts
  avg_risk: number
  max_risk: number
  open_findings: number
  top_findings: Finding[]
}

export type FindingsList = {
  findings: Finding[]
  total: number
  limit: number
  offset: number
}

export type AssetDetail = {
  asset: Asset
  findings: Finding[]
}

export type FindingStatus = "open" | "resolved" | "fp"

export type FindingsFilters = {
  severity?: string
  status?: string
  asset_id?: string
  scan_id?: string
  limit?: number
  offset?: number
}

export const api = {
  auth: {
    login: (email: string, password: string) =>
      request<{ access_token: string; token_type: string; mfa_required?: boolean; partial_token?: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    register: (email: string, password: string, name: string, companyName: string) =>
      request<{ id: string; email: string; name: string; tenant: { id: string; slug: string } }>("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password, name, company_name: companyName }),
      }),
    me: () => request<{ id: string; email: string; name: string; tenant: { id: string; slug: string } }>("/auth/me"),
    mfa: {
      setup: () => request<{ secret: string; provisioning_uri: string }>("/auth/mfa/setup"),
      verify: (code: string) =>
        request<{ success: boolean }>("/auth/mfa/verify", {
          method: "POST",
          body: JSON.stringify({ code }),
        }),
      disable: (password: string) =>
        request<{ success: boolean }>("/auth/mfa/disable", {
          method: "POST",
          body: JSON.stringify({ password }),
        }),
      challenge: (partialToken: string, code: string) =>
        request<{ access_token: string; token_type: string }>("/auth/mfa/challenge", {
          method: "POST",
          body: JSON.stringify({ partial_token: partialToken, code }),
          headers: { Authorization: `Bearer ${partialToken}` },
        }),
    },
  },
  asm: {
    listAssets: () => request<{ assets: Asset[] }>("/asm/assets"),
    scanDomain: (domain: string) =>
      request<{ scan: Scan; assets: Asset[] }>("/asm/scans", {
        method: "POST",
        body: JSON.stringify({ domain }),
      }),
    getResults: (scanId: string) =>
      request<{ scan: Scan; findings: Finding[] }>(`/asm/results/${scanId}`),
    getStats: () =>
      request<{ assets: number; findings: number; scans: number }>("/asm/stats"),
    getFindings: (filters: FindingsFilters = {}) => {
      const params = new URLSearchParams()
      if (filters.severity) params.set("severity", filters.severity)
      if (filters.status) params.set("status", filters.status)
      if (filters.asset_id) params.set("asset_id", filters.asset_id)
      if (filters.scan_id) params.set("scan_id", filters.scan_id)
      if (typeof filters.limit === "number") params.set("limit", String(filters.limit))
      if (typeof filters.offset === "number") params.set("offset", String(filters.offset))
      const qs = params.toString()
      return request<FindingsList>(`/asm/findings${qs ? `?${qs}` : ""}`)
    },
    getRiskSummary: () => request<RiskSummary>("/asm/risk-summary"),
    getAsset: (id: string) => request<AssetDetail>(`/asm/assets/${id}`),
    patchFinding: (id: string, status: FindingStatus) =>
      request<Finding>(`/asm/findings/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      }),
    enrichFinding: (id: string) =>
      request<Finding>(`/asm/findings/${id}/enrich`, {
        method: "POST",
      }),
    exportFindings: async (format: "csv" | "pdf") => {
      const res = await fetch(`${API_BASE}/asm/export?format=${format}`, {
        method: "GET",
        headers: buildHeaders(),
      })
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Error desconocido" }))
        throw new Error(error.detail || `HTTP ${res.status}`)
      }
      return res.blob()
    },
  },
  waitlist: {
    submit: (email: string, company?: string) =>
      request<{ id: string; email: string }>("/api/v1/waitlist", {
        method: "POST",
        body: JSON.stringify({ email, company }),
      }),
  },
  phishing: {
    campaigns: () => request<{ campaigns: unknown[] }>("/phishing/campaigns"),
    createCampaign: (data: unknown) =>
      request<{ id: string }>("/phishing/campaigns", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    results: (campaignId: string) =>
      request<unknown>(`/phishing/campaigns/${campaignId}/results`),
  },
}
