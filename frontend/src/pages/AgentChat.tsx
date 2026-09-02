import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { Bot, CheckCircle2, CircleAlert, Loader2, Plus, Send, Sparkles, User } from "lucide-react";
import Chart from "react-apexcharts";
import PageMeta from "../components/common/PageMeta";
import { askAgent, approveAgentRecommendation, type AgentChatEvidence, type AgentRecommendation, type AgentVisualization } from "../services/agent";

type Message = { id: string; role: "user" | "agent"; content: string; evidence?: AgentChatEvidence[]; visualizations?: AgentVisualization[]; recommendations?: AgentRecommendation[]; intent?: string; resources?: Array<{ name?: string; type?: string; location?: string; resource_id?: string; resource_group?: string; status?: string; provisioning_state?: string | null; configuration_status?: string | null }>; candidates?: Array<Record<string, unknown>>; currentConfiguration?: Record<string, unknown>; savingsAnalysis?: { monthly?: number | null; validated?: boolean }; summary?: { recommendation?: AgentRecommendation | string; savings?: number | null; confidence?: string; confidence_score?: number; next_step?: string; resource?: string | null; monthly_cost?: number | null; cost_status?: string; cost_source?: string }; error?: boolean };
const storageKey = "finops.agent.chat.history";
const suggestions = ["Which optimization should I do first?", "Show me the biggest savings opportunity", "Recommend optimizations for RG_GhadaMaalej."];

export default function AgentChat() {
  const [messages, setMessages] = useState<Message[]>(() => { try { return JSON.parse(sessionStorage.getItem(storageKey) ?? "[]") as Message[]; } catch { return []; } });
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [conversationContext, setConversationContext] = useState<Record<string, unknown>>({});
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => { sessionStorage.setItem(storageKey, JSON.stringify(messages)); endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);
  const send = async (event?: FormEvent) => {
    event?.preventDefault();
    const message = input.trim();
    if (!message || busy) return;
    const user: Message = { id: crypto.randomUUID(), role: "user", content: message };
    const next = [...messages, user];
    setMessages(next);
    setInput("");
    setBusy(true);
    setError("");
    try {
      const response = await askAgent(message, messages.slice(-4).map(({ role, content }) => ({ role: role === "agent" ? "assistant" : role, content })), conversationContext);
      if (response.conversation_state) {
        setConversationContext(response.conversation_state);
      } else if (response.resource_context?.resource_id) {
        setConversationContext({ active_resource: { name: response.resource_context.resource_name ?? response.resource_context.name, resource_id: response.resource_context.resource_id, resource_type: response.resource_context.resource_type ?? response.resource_context.type }, active_task: { intent: response.intent } });
      }
      const agentMessage: Message = {
        id: crypto.randomUUID(),
        role: "agent",
        content: response.answer,
        evidence: response.evidence,
        visualizations: response.visualizations,
        recommendations: response.recommendations,
        intent: response.intent,
        resources: response.resources,
        candidates: response.candidates,
        currentConfiguration: response.current_configuration,
        savingsAnalysis: typeof response.savings === "number" || response.savings == null ? { monthly: response.savings } : response.savings,
        summary: {
          recommendation: response.recommendation ?? undefined,
          savings: typeof response.savings === "number" || response.savings == null ? response.savings : response.savings.monthly,
          confidence: response.confidence,
          next_step: response.next_step,
          resource: response.resource,
          monthly_cost: response.monthly_cost,
          confidence_score: response.confidence_score,
          cost_status: response.cost_status,
          cost_source: response.cost_source,
        },
      };
      setMessages([...next, agentMessage]);
    } catch (reason) {
      const text = reason instanceof Error ? reason.message : "The FinOps Agent could not answer.";
      setError(text);
      setMessages([...next, { id: crypto.randomUUID(), role: "agent", content: text, error: true }]);
    } finally {
      setBusy(false);
    }
  };
  const approve = async (recommendation: AgentRecommendation) => { if (!recommendation.approval_enabled) return; setBusy(true); setError(""); try { const result = await approveAgentRecommendation(recommendation.recommendation_id); setMessages((current) => [...current, { id: crypto.randomUUID(), role: "agent", content: `${result.message} Execution status: ${result.status}${result.verification?.verification_status ? `. Verification: ${result.verification.verification_status}` : ""}.` }]); } catch (reason) { setError(reason instanceof Error ? reason.message : "Approval could not be recorded."); } finally { setBusy(false); };
  };
  const clear = () => { setMessages([]); setError(""); setConversationContext({}); sessionStorage.removeItem(storageKey); };
  return <><PageMeta title="FinOps Agent · Ask Agent" description="Ask the FinOps Agent about your Azure estate" /><div className="flex min-h-[calc(100vh-9rem)] flex-col gap-6"><header className="flex flex-wrap items-end justify-between gap-4"><div><div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-brand-500"><Sparkles size={15} /> FinOps Agent</div><h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Ask Agent</h1><p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Ask about costs, savings, recommendations, resources, security, governance, and agent activity.</p></div><button onClick={clear} disabled={!messages.length || busy} className="inline-flex items-center gap-2 rounded-lg border-gray-200 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-700 dark:text-gray-300"><Plus size={16} /> New conversation</button></header><section className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border-gray-200 bg-white shadow-theme-xs dark:border-gray-800 dark:bg-white/[0.03]"><div className="flex items-center gap-3 border-b border-gray-100 px-5 py-4 dark:border-gray-800"><div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-50 text-brand-600 dark:bg-brand-500/10"><Bot size={18} /></div><div><h2 className="text-sm font-semibold text-gray-900 dark:text-white">FinOps Agent</h2><p className="text-xs text-gray-500">Read-only answers from your persisted FinOps evidence</p></div></div><div className="flex-1 space-y-5 overflow-y-auto p-5">{!messages.length && <div className="mx-auto max-w-2xl py-10 text-center"><Sparkles className="mx-auto text-brand-500" size={28} /><h2 className="mt-4 text-lg font-semibold text-gray-900 dark:text-white">What would you like to understand?</h2><p className="mt-2 text-sm text-gray-500">The agent will answer from the connected subscription and will never execute remediation from chat.</p><div className="mt-6 grid gap-2 text-left sm:grid-cols-2">{suggestions.map((item) => <button key={item} onClick={() => setInput(item)} className="rounded-lg border-gray-200 p-3 text-sm text-gray-600 hover:border-brand-300 hover:text-brand-600 dark:border-gray-700 dark:text-gray-300">{item}</button>)}</div></div>}{messages.map((message) => <MessageBubble key={message.id} message={message} onApprove={approve} busy={busy} />)}{busy && <div className="flex items-center gap-3 text-sm text-gray-500"><Loader2 size={18} className="animate-spin text-brand-500" /><span className="animate-pulse">Reviewing persisted FinOps evidence...</span></div>}<div ref={endRef} /></div>{error && <div className="mx-5 mb-3 flex items-center gap-2 rounded-lg border-error-200 bg-error-50 px-3 py-2 text-sm text-error-700"><CircleAlert size={16} />{error}</div>}<form onSubmit={send} className="flex gap-3 border-t border-gray-100 p-4 dark:border-gray-800"><textarea value={input} onChange={(event) => setInput(event.target.value)} disabled={busy} rows={2} maxLength={4000} placeholder="Ask a FinOps question…" className="min-h-[52px] flex-1 resize-none rounded-lg border-gray-200 bg-transparent px-3 py-2.5 text-sm outline-none focus:border-brand-500 disabled:opacity-50 dark:border-gray-700 dark:text-white" /><button type="submit" disabled={busy || !input.trim()} className="inline-flex h-12 items-center gap-2 self-end rounded-lg bg-brand-500 px-4 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-50"><Send size={16} /> Send</button></form></section></div></>;
}

function formatEvidenceValue(value: unknown): string {
  if (value == null) return "-";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) return value.map((item) => formatEvidenceValue(item)).join("; ");
  if (typeof value === "object") return Object.entries(value as Record<string, unknown>).map(([key, item]) => `${key.replace(/_/g, " ")}: ${formatEvidenceValue(item)}`).join(" · ");
  return "[unavailable]";
}

function recommendationLabel(recommendation?: AgentRecommendation | string): string {
  if (!recommendation) return "No recommendation";
  if (typeof recommendation === "string") return recommendation;
  return recommendation.recommended_action ?? recommendation.finding ?? recommendation.problem_detected;
}

function MetricVisualization({ visualization }: { visualization: AgentVisualization }) {
  const historical = visualization.type === "line";
  const points = historical ? (visualization.series[0]?.data ?? []) : [];
  const labels = historical ? points.map((point) => point.timestamp) : visualization.series.map((item) => item.label ?? item.name ?? "Metric");
  const values = historical ? points.map((point) => point.value) : visualization.series.map((item) => item.value);
  const valid = labels.length > 0 && values.length > 0 && values.every((value) => typeof value === "number" && Number.isFinite(value));
  if (!valid) return null;
  const options = { chart: { toolbar: { show: false }, zoom: { enabled: false }, animations: { enabled: false } }, xaxis: { categories: labels, labels: { rotate: historical ? -35 : 0 } }, yaxis: { title: { text: visualization.unit } }, dataLabels: { enabled: false }, stroke: { curve: "smooth" as const } };
  return <div className="my-4 rounded-lg border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-900"><div className="mb-2 flex items-center justify-between gap-3"><b className="text-xs uppercase tracking-wide text-gray-600 dark:text-gray-300">{visualization.title}</b><span className="text-xs text-gray-500">{visualization.unit}</span></div><Chart
  type={historical ? "line" : "bar"}
  height={220}
  options={options}
  series={[{ name: visualization.unit, data: values as number[] }]}
  width="100%"
/>
</div>;
}

function MessageBubble({ message, onApprove, busy }: { message: Message; onApprove: (recommendation: AgentRecommendation) => void; busy: boolean }) { return <div className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}><div className={`max-w-3xl rounded-xl px-4 py-3 text-sm ${message.role === "user" ? "bg-brand-500 text-white" : message.error ? "border border-error-200 bg-error-50 text-error-700" : "border border-gray-200 bg-gray-50 text-gray-700 dark:border-gray-700 dark:bg-gray-800/50 dark:text-gray-200"}`}><div className="mb-1 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wide opacity-70">{message.role === "user" ? <User size={13} /> : <Bot size={13} />}{message.role === "user" ? "You" : "Agent"}</div><p className="whitespace-pre-wrap leading-6">{message.content}</p>{message.visualizations?.map((visualization, index) => <MetricVisualization key={`${visualization.title}-${index}`} visualization={visualization} />)}{["resource_listing", "resource_status", "inventory"].includes(message.intent ?? "") && message.resources?.length ? <div className="mt-4 overflow-x-auto"><table className="w-full text-left text-xs"><thead><tr><th className="p-2">Name</th><th className="p-2">Type</th><th className="p-2">Location</th><th className="p-2">Status</th><th className="p-2">Resource ID</th></tr></thead><tbody>{message.resources.map((item) => <tr key={item.resource_id} className="border-t border-gray-200 dark:border-gray-700"><td className="p-2 font-medium">{item.name ?? "-"}</td><td className="p-2">{item.type ?? "-"}</td><td className="p-2">{item.location ?? "-"}</td><td className="p-2">{item.status ?? item.provisioning_state ?? "-"}</td><td className="p-2 break-all">{item.resource_id ?? "-"}</td></tr>)}</tbody></table></div> : null}{message.intent === "sku_comparison" || message.intent === "savings_analysis" ? <div className="mt-4 overflow-x-auto"><table className="w-full text-left text-xs"><thead><tr><th className="p-2">Candidate SKU</th><th className="p-2">Monthly cost</th><th className="p-2">Savings</th><th className="p-2">Pricing</th></tr></thead><tbody>{message.candidates?.map((item, index) => <tr key={`${String(item.sku)}-${index}`} className="border-t border-gray-200 dark:border-gray-700"><td className="p-2 font-medium">{String(item.sku ?? "-")}</td><td className="p-2">{item.monthly_cost == null ? "-" : `$${Number(item.monthly_cost).toFixed(2)}`}</td><td className="p-2">{item.estimated_savings == null ? "Savings not quantifiable" : `$${Number(item.estimated_savings).toFixed(2)}`}</td><td className="p-2">{item.validated ? "Validated" : "Unavailable"}</td></tr>)}</tbody></table></div> : null}{message.role === "agent" && message.summary && !["metrics", "metrics_history", "resource_listing", "sku_comparison", "savings_analysis"].includes(message.intent ?? "") ? <div className="mt-4 grid gap-2 sm:grid-cols-2"><div className="rounded-md bg-white/70 p-3 dark:bg-black/10"><b>Recommendation</b><div>{typeof message.summary.recommendation === "string" ? message.summary.recommendation : recommendationLabel(message.summary.recommendation)}</div><div className="mt-1 text-xs opacity-70">Resource: {message.summary.resource ?? "-"}</div></div><div className="rounded-md bg-white/70 p-3 dark:bg-black/10"><b>Monthly cost</b><div>{message.summary.monthly_cost == null ? "-" : `$${message.summary.monthly_cost.toFixed(2)}`}</div></div><div className="rounded-md bg-white/70 p-3 dark:bg-black/10"><b>Potential savings</b><div>{message.summary.savings == null ? "Savings not quantifiable" : `$${message.summary.savings.toFixed(2)}/month`}</div></div><div className="rounded-md bg-white/70 p-3 dark:bg-black/10"><b>Cost evidence</b><div>{message.summary.cost_status ?? "Unavailable"} · {message.summary.cost_source ?? "none"}</div></div><div className="rounded-md bg-white/70 p-3 dark:bg-black/10"><b>Confidence</b><div>{message.summary.confidence_score == null ? message.summary.confidence ?? "-" : `${message.summary.confidence_score}% — ${message.summary.confidence ?? "-"}`}</div></div><div className="rounded-md bg-white/70 p-3 sm:col-span-2 dark:bg-black/10"><b>Next step</b><div>{message.summary.next_step ?? "-"}</div></div></div> : null}{message.recommendations?.length ? <div className="mt-4 space-y-3">{message.recommendations.map((item) => <div key={`${item.recommendation_id}-${item.resource_id}`} className="rounded-lg border-gray-200 bg-white p-3 text-xs dark:border-gray-700 dark:bg-gray-900/40"><div className="flex items-start justify-between gap-3"><strong className="text-sm">{item.resource}</strong>{item.approved ? <CheckCircle2 size={16} className="text-success-500" /> : null}</div><div className="mt-2 grid gap-1 text-gray-600 dark:text-gray-300"><span><b>Resource group:</b> {item.resource_group ?? "-"}</span><span><b>Problem:</b> {item.problem_detected}</span><span><b>Action:</b> {item.recommended_action}</span><span><b>Current estimated cost:</b> {item.current_estimated_cost == null ? "-" : `$${item.current_estimated_cost.toFixed(2)}`}</span><span><b>Estimated monthly savings:</b> {item.estimated_monthly_savings == null ? "-" : `$${item.estimated_monthly_savings.toFixed(2)}`}</span><span><b>Risk / confidence:</b> {item.risk} / {(item.confidence * 100).toFixed(0)}%</span></div><button disabled={busy || !item.approval_enabled} onClick={() => onApprove(item)} className="mt-3 inline-flex items-center gap-2 rounded-lg bg-brand-500 px-3 py-2 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50">{item.approved ? <CheckCircle2 size={14} /> : <Send size={14} />} {item.approved ? "Approved" : item.approval_enabled ? "Approve" : item.approval_disabled_reason ?? "Read-only"}</button></div>)}</div> : null}{message.evidence?.length ? <div className="mt-3 space-y-2 border-t border-current/10 pt-3">{message.evidence.map((item, index) => <div key={index} className="rounded-md bg-white/60 p-2 text-xs dark:bg-black/10"><strong>{item.label ?? "Evidence"}:</strong> <span className="whitespace-pre-wrap break-words">{formatEvidenceValue(item.value ?? item.resource_name ?? item.resource_id ?? item.status)}</span>{item.resource_id && item.value != null ? ` · ${item.resource_id}` : ""}{item.savings != null ? ` · Savings ${item.savings}` : ""}</div>)}</div> : null}</div></div>; }
