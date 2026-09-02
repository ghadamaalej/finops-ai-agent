import { getIdentityToken } from "../lib/entra";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type AgentAction = {
  id: string; recommendation_id: string | null; resource_id: string; resource_name: string; action: string | null;
  status: string | null; verification_status: string | null; verification_message: string | null;
  potential_savings: number | null; realized_savings: number | null; rollback: Record<string, unknown>; timestamp: string | null;
  audit: Record<string, unknown>;
};
export type AgentChatEvidence = { label?: string; value?: unknown; resource_id?: string; resource_name?: string; action?: string; cost?: number | null; savings?: number | null; status?: string; verification?: string; metric_name?: string; unit?: string; period?: string; source?: string; collected_at?: string | null };
export type AgentVisualization = { type: "bar" | "line"; title: string; unit: string; series: Array<{ label?: string; value?: number; name?: string; data?: Array<{ timestamp: string; value: number }> }>; };
export type AgentRecommendation = { recommendation_id: string; resource_id: string; resource: string; resource_group: string | null; problem_detected: string; finding?: string | null; action?: string | null; recommended_action: string | null; current_estimated_cost: number | null; cost?: number | null; cost_status: string; cost_source: string; cost_type?: string | null; is_estimated: boolean; estimated_monthly_savings: number | null; potential_savings?: number | null; savings_status: string; evidence?: Record<string, unknown>; risk: string; confidence: number; executable: boolean; approval_enabled: boolean; approval_disabled_reason: string | null; approved: boolean };
export type AgentChatResource = { name?: string; type?: string; location?: string; resource_id?: string; resource_group?: string; status?: string; provisioning_state?: string | null; configuration_status?: string | null };
export type AgentChatSavings = number | null | { monthly?: number | null; validated?: boolean };
export type AgentChatResponse = { answer: string; intent?: string; status?: string; recommendation?: AgentRecommendation | string | null; evidence: AgentChatEvidence[]; visualizations?: AgentVisualization[]; resources?: AgentChatResource[]; cost?: { monthly?: number | null; currency?: string; scope?: string }; savings?: AgentChatSavings; confidence?: string; resource_context?: { resource_id?: string; resource_name?: string; resource_type?: string; resource_group?: string; name?: string; type?: string; current_sku?: string }; conversation_state?: Record<string, unknown>; current_configuration?: Record<string, unknown>; candidates?: Array<Record<string, unknown>>; best_candidate?: Record<string, unknown>; diagnostics?: Record<string, unknown>; confidence_score?: number; confidence_level?: string; data_quality?: Record<string, unknown>; next_step?: string; resource?: string | null; resource_id?: string | null; monthly_cost?: number | null; cost_status?: string; cost_source?: string; request_id?: string; recommendations: AgentRecommendation[]; subscription_id: string; read_only: boolean };
export type AgentApprovalResponse = { recommendation_id: string; approved: boolean; execution_started: boolean; status: string; message: string; verification?: { verification_status?: string; message?: string } };

export type AgentOverviewData = {
  generated_at: string; subscription_id: string;
  savings: { potential_monthly: number; realized_monthly: number | null; verified_actions: number };
  resources: { total: number | null; optimization_candidates: number };
  agent: { status: string; recommendations: number; pending_approval: number; executed: number; verification_pending: number };
  cost_overview: { trend: Array<{ timestamp: string; monthly_cost: number }> };
  opportunities: { total: number; items: Array<{ id: string; resource_id: string; resource_name: string | null; action: string | null; potential_savings: number | null; confidence: number | null; approved: boolean }> };
  pending_approvals: Array<{ id: string; resource_id: string; resource_name: string | null; action: string | null; potential_savings: number | null; confidence: number | null }>;
  actions: AgentAction[];
  activity: Record<string, { status: string; count?: number; resources?: number }>;
  audit: { generated_at: string; subscription_id: string; action_count: number };
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, { ...init, headers: { "Content-Type": "application/json", Authorization: `Bearer ${getIdentityToken()}`, ...init?.headers } });
  if (!response.ok) { const body = await response.json().catch(() => null) as { detail?: string } | null; throw new Error(body?.detail ?? "Unable to load agent data."); }
  return response.json() as Promise<T>;
}
export const getAgentOverview = (signal?: AbortSignal) => request<AgentOverviewData>("/api/agent/overview", { signal });
export const getAgentActions = (page: number, pageSize = 4) => request<{ items: AgentAction[]; total: number }>(`/api/agent/actions?page=${page}&page_size=${pageSize}`);
export const approveAgentRecommendation = (id: string) => request<AgentApprovalResponse>(`/api/agent/recommendations/${encodeURIComponent(id)}/approve`, { method: "POST", body: JSON.stringify({}) });
export const rollbackAgentExecution = (id: string) => request<{ message: string }>(`/api/agent/executions/${encodeURIComponent(id)}/rollback`, { method: "POST" });
export const askAgent = (message: string, history: Array<{ role: "user" | "assistant"; content: string }>, conversationContext?: Record<string, unknown>) => request<AgentChatResponse>("/api/agent/chat", { method: "POST", body: JSON.stringify({ message, history, conversation_context: conversationContext ?? {} }) });
