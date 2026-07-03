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

export const api = {
  auth: {
    login: (email: string, password: string) =>
      request<{ access_token: string; token_type: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    register: (email: string, password: string, name: string) =>
      request<{ id: string; email: string; name: string }>("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password, name }),
      }),
    me: () => request<{ id: string; email: string; name: string }>("/auth/me"),
  },
  asm: {
    list: () => request<{ assets: any[] }>("/asm/assets"),
    scan: (assetId: string) =>
      request<{ scan_id: string }>(`/asm/scan/${assetId}`, { method: "POST" }),
    results: (scanId: string) =>
      request<{ findings: any[] }>(`/asm/results/${scanId}`),
  },
  phishing: {
    campaigns: () => request<{ campaigns: any[] }>("/phishing/campaigns"),
    createCampaign: (data: any) =>
      request<{ id: string }>("/phishing/campaigns", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    results: (campaignId: string) =>
      request<any>(`/phishing/campaigns/${campaignId}/results`),
  },
}
