import { getIdentityToken } from "../lib/entra";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type DashboardSummary = {
  generated_at: string; subscription_id: string;
  cost: { monthly: number | null; previous: number | null; change_percent: number | null; forecast: number | null; currency: string | null; cost_source: string | null; cost_type: string | null; is_estimated: boolean | null };
  savings: { potential_monthly: number; realized_monthly: number | null; verified_actions: number };
  resources: { total: number | null; underutilized: number | null; high_risk: number | null; optimization_candidates: number };
  resource_inventory: Array<{ resource_id: string; resource_name: string | null; resource_type: string | null; resource_group: string | null; location: string | null; sku: string | null; vm_size: string | null; configuration: Record<string, unknown>; provisioning_state: string | null; configuration_status: string }>;
  resource_diagnostics: Array<{ resource_id: string; resource_name: string | null; cost_status: string; cost_source: string; utilization_status: string; utilization_reason: string; configuration_status: string; recommendation_status: string; missing_data: string[] }>;
  agent: { status: string; recommendations: number; pending_approval: number; executed: number; verification_pending: number };
  cost_overview: { trend: Array<{ timestamp: string; monthly_cost: number }> };
  cost_by_resource: Array<{ resource_id: string; resource_name: string | null; service_name: string | null; resource_group: string | null; points: Array<{ timestamp: string; monthly_cost: number }> }>;
  cost_composition: Array<{ name: string; monthly_cost: number }>;
  cost_drivers: Array<{ resource_id: string; resource_name: string | null; resource_type: string | null; service_name: string | null; monthly_cost: number | null; percent_of_total: number | null }>;
  cost_resources: Array<{ resource_id: string; resource_name: string | null; resource_type: string | null; service_name: string | null; resource_group: string | null; monthly_cost: number | null; percent_of_total: number | null; cost_source?: string | null; cost_type?: string | null; is_estimated?: boolean | null; cost_status?: string | null }>;
  optimization_opportunities: Array<{ category: string; count: number; potential_savings: number }>;
  recommendations: Array<{ recommendation_id: string; resource_id: string; resource_name: string | null; action: string | null; potential_savings: number | null; confidence: number | null; approved: boolean }>;
  security: { score: number | null; critical: number | null; high: number | null; total: number | null };
  governance: { compliance: number | null; violations: number | null; affected_resources: number | null };
  performance: { average_cpu: number | null; underutilized: number | null; overutilized: number | null };
  recent_actions: Array<{ action: string | null; resource_id: string; execution_status: string | null; verification_status: string | null; realized_savings: number | null; timestamp: string | null }>;
  alerts: Array<{ severity: string; title: string; description: string }>;
};

export type DashboardRefreshResult = {
  subscription_id: string;
  resources_collected: number;
  cost_records_collected: number;
  cost_records_persisted: number;
  cache_rows_persisted: number;
  history_rows_persisted: number;
  cost_source: string | null;
  cost_type: string | null;
  is_estimated: boolean | null;
};

export type ResourceInventoryResponse = {
  items: Array<DashboardSummary["resource_inventory"][number] & { status: string; power_state: string | null; monthly_cost: number | null; cost_source: string; cost_type: string | null; cost_status: string; is_estimated: boolean }>;
  page: number; page_size: number; total: number; has_next: boolean; has_previous: boolean;
};

export async function getResourceInventory(params: { page: number; pageSize: number; search?: string; resourceType?: string; resourceGroup?: string; region?: string; status?: string }, signal?: AbortSignal): Promise<ResourceInventoryResponse> {
  const query = new URLSearchParams({ page: String(params.page), page_size: String(params.pageSize) });
  if (params.search) query.set("search", params.search);
  if (params.resourceType && params.resourceType !== "all") query.set("resource_type", params.resourceType);
  if (params.resourceGroup && params.resourceGroup !== "all") query.set("resource_group", params.resourceGroup);
  if (params.region && params.region !== "all") query.set("region", params.region);
  if (params.status && params.status !== "all") query.set("status", params.status);
  const response = await fetch(`${apiBaseUrl}/api/dashboard/resources?${query}`, { headers: { Authorization: `Bearer ${getIdentityToken()}` }, signal });
  if (!response.ok) { const body = await response.json().catch(() => null) as { detail?: string } | null; throw new Error(body?.detail ?? "Unable to load resource inventory."); }
  return response.json() as Promise<ResourceInventoryResponse>;
}

export type ResourceDetails = {
  resource: { identity: Record<string, string | null>; configuration: Record<string, unknown>; runtime: Record<string, string | null> };
  metrics: { status: string; period: string | null; source: string; collected_at: string | null; values: Record<string, { value: number | string | null; status: string; source: string | null; period: string | null; collected_at: string | null; reason: string | null }> };
  cost: { monthly: number | null; hourly_estimated: number | null; currency: string | null; source: string | null; type: string | null; is_estimated: boolean | null; status: string };
  finops: { utilization: string; recommendations: Array<{ action: string | null; category: string | null; recommended_action: string | null; estimated_monthly_savings: number | null; risk: string; confidence: number | null; evidence: string }> };
  security: { scope: string; status: string; findings: Array<Record<string, unknown>>; reason: string | null };
  governance: { scope: string; status: string; policy_violations: unknown[]; compliance: number | null; reason: string | null };
  evidence: Record<string, unknown>;
};

export async function getResourceDetails(resourceId: string, signal?: AbortSignal): Promise<ResourceDetails> {
  const response = await fetch(`${apiBaseUrl}/api/dashboard/resources/details?resource_id=${encodeURIComponent(resourceId)}`, { headers: { Authorization: `Bearer ${getIdentityToken()}` }, signal });
  if (!response.ok) { const body = await response.json().catch(() => null) as { detail?: string } | null; throw new Error(body?.detail ?? "Unable to load resource details."); }
  return response.json() as Promise<ResourceDetails>;
}

export async function getDashboardSummary(signal?: AbortSignal): Promise<DashboardSummary> {
  const response = await fetch(`${apiBaseUrl}/api/dashboard/summary`, { headers: { Authorization: `Bearer ${getIdentityToken()}` }, signal });
  if (!response.ok) { const body = await response.json().catch(() => null) as { detail?: string } | null; throw new Error(body?.detail ?? "Unable to load dashboard data."); }
  return response.json() as Promise<DashboardSummary>;
}

export async function refreshDashboardCosts(azureAccessToken: string): Promise<DashboardRefreshResult> {
  const response = await fetch(`${apiBaseUrl}/api/dashboard/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${getIdentityToken()}` },
    body: JSON.stringify({ azure_access_token: azureAccessToken }),
  });
  if (!response.ok) { const body = await response.json().catch(() => null) as { detail?: string } | null; throw new Error(body?.detail ?? "Unable to refresh Azure cost data."); }
  return response.json() as Promise<DashboardRefreshResult>;
}
