const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
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
  discovered_at: string
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
      setup: () => request<{ secret: string; uri: string }>("/auth/mfa/setup"),
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
