import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router";
import { useMsal } from "@azure/msal-react";
import { getAzureManagementAccessToken } from "../lib/entra";
import { Activity, AlertTriangle, ChevronRight, Database, DollarSign, RefreshCw, Search, Server, ShieldCheck } from "lucide-react";
import PageMeta from "../components/common/PageMeta";
import { getDashboardSummary, getResourceDetails, getResourceInventory, type DashboardSummary, type ResourceDetails } from "../services/dashboard";

type Resource = DashboardSummary["resource_inventory"][number];
type StatusFilter = "all" | "active" | "other";

function formatAmount(value: number | null | undefined, currency: string) {
  return value == null ? "No cost data" : new Intl.NumberFormat("en-US", { style: "currency", currency, maximumFractionDigits: 2 }).format(value);
}

function normalized(value: string | null | undefined) { return value?.trim() || "Unavailable"; }
function isActive(resource: Resource) { return ["running", "succeeded", "available", "active"].includes((resource.provisioning_state ?? "").toLowerCase()); }

function Kpi({ label, value, detail, Icon }: { label: string; value: string; detail: string; Icon: typeof Server }) {
  return <article className="rounded-lg border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]"><div className="flex items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{label}</p><p className="mt-3 text-2xl font-semibold text-gray-900 dark:text-white">{value}</p></div><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-300"><Icon size={18} /></span></div><p className="mt-2 text-xs text-gray-500 dark:text-gray-400">{detail}</p></article>;
}

export default function ActiveResources() {
  const { accounts } = useMsal();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [type, setType] = useState("all");
  const [group, setGroup] = useState("all");
  const [region, setRegion] = useState("all");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [details, setDetails] = useState<ResourceDetails | null>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsError, setDetailsError] = useState("");
  const [detailsTab, setDetailsTab] = useState("Overview");
  const [page, setPage] = useState(1);
  const pageSize = 25;
  const [inventoryPage, setInventoryPage] = useState<{ items: Resource[]; total: number; has_next: boolean; has_previous: boolean }>({ items: [], total: 0, has_next: false, has_previous: false });

  const load = useCallback(async () => { setLoading(true); try { const [nextSummary, nextPage] = await Promise.all([getDashboardSummary(), getResourceInventory({ page, pageSize, search: query, resourceType: type, resourceGroup: group, region, status })]); setSummary(nextSummary); setInventoryPage(nextPage); setError(""); } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to load resource inventory."); } finally { setLoading(false); } }, [group, page, pageSize, query, region, status, type]);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => { setPage(1); }, [query, type, group, region, status]);
  useEffect(() => {
    if (!selectedId) {
      setDetails(null);
      return;
    }

    const account = accounts[0];

    if (!account) {
      setDetailsError(
        "Your Microsoft sign-in session expired. Please sign in again."
      );
      return;
    }

    const controller = new AbortController();

    setDetailsLoading(true);
    setDetailsError("");
    setDetailsTab("Overview");

    void getAzureManagementAccessToken(account)
      .then((azureAccessToken) =>
        getResourceDetails(
          selectedId,
          azureAccessToken,
          controller.signal
        )
      )
      .then(setDetails)
      .catch((reason) => {
        if (!controller.signal.aborted) {
          setDetailsError(
            reason instanceof Error
              ? reason.message
              : "Unable to load resource details."
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setDetailsLoading(false);
        }
      });

    return () => controller.abort();
  }, [selectedId, accounts]);

  const inventory = inventoryPage.items;
  const costs = useMemo(() => new Map((summary?.cost_resources ?? []).map((item) => [item.resource_id.toLowerCase(), item])), [summary]);
  const diagnostics = useMemo(() => new Map((summary?.resource_diagnostics ?? []).map((item) => [item.resource_id.toLowerCase(), item])), [summary]);
  const recommendations = useMemo(() => new Map((summary?.recommendations ?? []).map((item) => [item.resource_id.toLowerCase(), item])), [summary]);
  const types = useMemo(() => [...new Set(inventory.map((item) => normalized(item.resource_type)))].sort(), [inventory]);
  const groups = useMemo(() => [...new Set(inventory.map((item) => normalized(item.resource_group)))].sort(), [inventory]);
  const regions = useMemo(() => [...new Set(inventory.map((item) => normalized(item.location)))].sort(), [inventory]);
  const filtered = inventory;
  const selected = inventory.find((item) => item.resource_id === selectedId) ?? null;
  const currency = summary?.cost.currency ?? "USD";
  const totalCost = [...costs.values()].reduce((sum, item) => sum + (item.monthly_cost ?? 0), 0);
  const activeCount = inventoryPage.total;

  if (loading && !summary) return <div className="p-8 text-sm text-gray-500">Loading active resources...</div>;
  if (error && !summary) return <div className="rounded-lg border-red-200 bg-red-50 p-5 text-sm text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">{error}</div>;

  return <><PageMeta title="FinOps Agent · Active Resources" description="Azure resource inventory and evidence" /><div className="space-y-6"><header className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-medium text-brand-500">RESOURCE INVENTORY</p><h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">Active Resources</h1><p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Resources discovered in the connected subscription. Issues and recommendations remain separate evidence.</p></div><button type="button" onClick={() => void load()} disabled={loading} className="inline-flex items-center gap-2 rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-60"><RefreshCw size={16} className={loading ? "animate-spin" : ""} />Refresh</button></header>{error && <div className="rounded-lg border-amber-200 bg-amber-50 p-4 text-sm text-amber-700 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-300">Showing the last successful result. Refresh failed: {error}</div>}
             {selectedId && <section className="rounded-lg border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-wider text-brand-500">Resource observability</p><h2 className="mt-1 text-xl font-semibold text-gray-900 dark:text-white">{normalized(selected?.resource_name)}</h2><p className="mt-1 break-all text-xs text-gray-500">{selectedId}</p></div><button type="button" onClick={() => setSelectedId(null)} className="text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white">Close</button></div>{detailsLoading && <p className="mt-6 text-sm text-gray-500">Loading resource evidence...</p>}{detailsError && <p className="mt-6 rounded-lg bg-red-50 p-3 text-sm text-red-700">{detailsError}</p>}{details && <><nav className="mt-6 flex gap-2 overflow-x-auto border-b border-gray-200 dark:border-gray-800">{["Overview", "Usage & Metrics", "Cost", "FinOps", "Security", "Governance", "Evidence"].map((tab) => <button key={tab} type="button" onClick={() => setDetailsTab(tab)} className={`whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium ${detailsTab === tab ? "border-brand-500 text-brand-600" : "border-transparent text-gray-500"}`}>{tab}</button>)}</nav><div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">{detailsTab === "Overview" && Object.entries({...details.resource.identity, ...details.resource.runtime, sku: details.resource.configuration.sku, os_type: details.resource.configuration.os_type, monthly_cost: details.cost.monthly}).map(([label, value]) => <div key={label} className="rounded-lg bg-gray-50 p-4 dark:bg-white/[0.04]"><p className="text-xs uppercase text-gray-500">{label.replace(/_/g, " ")}</p><p className="mt-2 break-words font-semibold text-gray-900 dark:text-white">{value == null || value === "" ? "Unavailable" : String(value)}</p></div>)}{detailsTab === "Usage & Metrics" && Object.entries(details.metrics.values).map(([label, evidence]) => <div key={label} className="rounded-lg bg-gray-50 p-4 dark:bg-white/[0.04]"><p className="text-xs uppercase text-gray-500">{label.replace(/_/g, " ")}</p><p className="mt-2 font-semibold text-gray-900 dark:text-white">{evidence.value == null ? "Unavailable" : String(evidence.value)}</p><p className="mt-1 text-xs text-gray-500">{evidence.status} · {evidence.source ?? "No source"} · {evidence.period ?? "No period"}{evidence.reason ? ` · ${evidence.reason}` : ""}</p></div>)}{detailsTab === "Cost" && <div className="rounded-lg bg-gray-50 p-4 dark:bg-white/[0.04]"><p className="text-xs uppercase text-gray-500">Monthly cost</p><p className="mt-2 text-xl font-semibold text-gray-900 dark:text-white">{formatAmount(details.cost.monthly, details.cost.currency ?? currency)}</p><p className="mt-1 text-xs text-gray-500">{details.cost.source ?? "Unavailable"} · {details.cost.type ?? details.cost.status}</p></div>}{detailsTab === "FinOps" && <div className="col-span-full"><p className="text-sm text-gray-500">Utilization: {details.finops.utilization}</p>{details.finops.recommendations.length ? details.finops.recommendations.map((item, index) => <div key={`${item.action}-${index}`} className="mt-3 rounded-lg bg-gray-50 p-4 dark:bg-white/[0.04]"><p className="font-semibold text-gray-900 dark:text-white">{item.recommended_action ?? "Recommendation"}</p><p className="mt-1 text-sm text-gray-500">Savings: {item.estimated_monthly_savings == null ? "Unavailable" : formatAmount(item.estimated_monthly_savings, details.cost.currency ?? currency)} · confidence {item.confidence ?? "Unavailable"}</p></div>) : <p className="mt-4 text-sm text-gray-500">No resource-scoped recommendation available.</p>}</div>}{(detailsTab === "Security" || detailsTab === "Governance") && <div className="col-span-full rounded-lg bg-gray-50 p-4 text-sm dark:bg-white/[0.04]"><p className="font-semibold text-gray-900 dark:text-white">{detailsTab} evidence: {detailsTab === "Security" ? details.security.status : details.governance.status}</p><p className="mt-2 text-gray-500">{detailsTab === "Security" ? details.security.reason : details.governance.reason}</p></div>}{detailsTab === "Evidence" && <pre className="col-span-full overflow-auto rounded-lg bg-gray-900 p-4 text-xs text-gray-100">{JSON.stringify(details.evidence, null, 2)}</pre>}</div></>}</section>}
      +       <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Kpi label="Total resources" value={String(inventory.length)} detail="Discovered resource inventory" Icon={Server} /><Kpi label="Running / active" value={String(activeCount)} detail="Based on provisioning state" Icon={Activity} /><Kpi label="Monthly estimated cost" value={formatAmount(totalCost, currency)} detail={summary?.cost.is_estimated ? "Estimated cost evidence" : "Persisted cost evidence"} Icon={DollarSign} /><Kpi label="Resource types" value={String(types.length)} detail="Unique resource types discovered" Icon={Database} /></div>
      <section className="rounded-lg border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]"><div className="mb-5 flex-wrap items-end justify-between gap-3"><div><h2 className="font-semibold text-gray-900 dark:text-white">Resource inventory</h2><p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{inventoryPage.total} resources match the current filters. Page {page}.</p></div></div><div className="mb-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5"><label className="relative xl:col-span-1"><Search className="pointer-events-none absolute left-3 top-3 text-gray-400" size={16} /><input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search resources" className="w-full rounded-lg border-gray-200 bg-white py-2 pl-9 pr-3 text-sm text-gray-900 outline-none focus:border-brand-500 dark:border-gray-700 dark:bg-gray-900 dark:text-white" /></label><label><span className="sr-only">Resource type</span><select value={type} onChange={(event) => setType(event.target.value)} className="w-full rounded-lg border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"><option value="all">All types</option>{types.map((value) => <option key={value}>{value}</option>)}</select></label><label><span className="sr-only">Resource group</span><select value={group} onChange={(event) => setGroup(event.target.value)} className="w-full rounded-lg border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"><option value="all">All resource groups</option>{groups.map((value) => <option key={value}>{value}</option>)}</select></label><label><span className="sr-only">Region</span><select value={region} onChange={(event) => setRegion(event.target.value)} className="w-full rounded-lg border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"><option value="all">All regions</option>{regions.map((value) => <option key={value}>{value}</option>)}</select></label><label><span className="sr-only">Status</span><select value={status} onChange={(event) => setStatus(event.target.value as StatusFilter)} className="w-full rounded-lg border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"><option value="all">All statuses</option><option value="active">Running / active</option><option value="other">Other states</option></select></label></div><div className="overflow-x-auto"><table className="w-full min-w-[1000px] text-left text-sm"><thead className="border-b border-gray-200 text-xs uppercase tracking-wider text-gray-500 dark:border-gray-800"><tr><th className="pb-3 pr-4">Resource</th><th className="pb-3 pr-4">Type</th><th className="pb-3 pr-4">Status</th><th className="pb-3 pr-4">Resource group</th><th className="pb-3 pr-4">Region</th><th className="pb-3 pr-4">SKU</th><th className="pb-3 pr-4 text-right">Monthly cost</th><th className="pb-3" /></tr></thead><tbody>{filtered.length ? filtered.map((item) => { const cost = costs.get(item.resource_id.toLowerCase()); return <tr key={item.resource_id} onClick={() => setSelectedId(item.resource_id)} className="cursor-pointer border-b border-gray-50 transition hover:bg-gray-50 dark:border-gray-800/60 dark:hover:bg-white/[0.03]"><td className="max-w-[230px] py-4 pr-4"><p className="truncate font-semibold text-gray-900 dark:text-white">{normalized(item.resource_name)}</p><p className="mt-0.5 truncate text-xs text-gray-500">{item.resource_id}</p></td><td className="max-w-[160px] truncate py-4 pr-4 text-gray-600 dark:text-gray-300">{normalized(item.resource_type)}</td><td className="py-4 pr-4"><span className={`rounded-full px-2.5 py-1 text-xs font-medium ${isActive(item) ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300" : "bg-gray-100 text-gray-600 dark:bg-white/10 dark:text-gray-300"}`}>{normalized(item.provisioning_state)}</span></td><td className="py-4 pr-4 text-gray-600 dark:text-gray-300">{normalized(item.resource_group)}</td><td className="py-4 pr-4 text-gray-600 dark:text-gray-300">{normalized(item.location)}</td><td className="py-4 pr-4 text-gray-600 dark:text-gray-300">{normalized(item.sku)}</td><td className="py-4 pr-4 text-right font-semibold text-gray-900 dark:text-white">{formatAmount(cost?.monthly_cost, currency)}</td><td className="py-4"><ChevronRight size={18} className="text-gray-400" /></td></tr>; }) : <tr><td colSpan={8} className="py-12 text-center text-sm text-gray-500">No resources match the selected filters.</td></tr>}</tbody></table></div><div className="mt-5 flex items-center justify-between gap-3 border-t border-gray-100 pt-4 text-sm dark:border-gray-800"><span className="text-gray-500">Showing {inventoryPage.total === 0 ? 0 : (page - 1) * pageSize + 1}–{Math.min(page * pageSize, inventoryPage.total)} of {inventoryPage.total}</span><div className="flex gap-2"><button type="button" disabled={!inventoryPage.has_previous || loading} onClick={() => setPage((value) => value - 1)} className="rounded-lg border-gray-200 px-3 py-2 disabled:opacity-40 dark:border-gray-700">Previous</button><button type="button" disabled={!inventoryPage.has_next || loading} onClick={() => setPage((value) => value + 1)} className="rounded-lg border-gray-200 px-3 py-2 disabled:opacity-40 dark:border-gray-700">Next</button></div></div></section>
             {false && selected && (() => { const cost = costs.get(selected!.resource_id.toLowerCase()); const diagnostic = diagnostics.get(selected!.resource_id.toLowerCase()); const recommendation = recommendations.get(selected!.resource_id.toLowerCase()); const missing = diagnostic?.missing_data ?? []; return <section className="rounded-lg border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-wider text-brand-500">Resource details</p><h2 className="mt-1 text-xl font-semibold text-gray-900 dark:text-white">{normalized(selected!.resource_name)}</h2><p className="mt-1 break-all text-xs text-gray-500">{selected!.resource_id}</p></div><button type="button" onClick={() => setSelectedId(null)} className="text-sm font-medium text-gray-500 hover:text-gray-900 dark:hover:text-white">Close</button></div><div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4"><div className="rounded-lg bg-gray-50 p-4 dark:bg-white/[0.04]"><p className="text-xs font-medium text-gray-500">Monthly cost</p><p className="mt-1 font-semibold text-gray-900 dark:text-white">{formatAmount(cost?.monthly_cost, currency)}</p><p className="mt-1 text-xs text-gray-500">{cost?.cost_source ?? diagnostic?.cost_source ?? "Cost source unavailable"} · {cost?.cost_type ?? diagnostic?.cost_status ?? "unavailable"}</p></div><div className="rounded-lg bg-gray-50 p-4 dark:bg-white/[0.04]"><p className="text-xs font-medium text-gray-500">Utilization</p><p className="mt-1 font-semibold capitalize text-gray-900 dark:text-white">{diagnostic?.utilization_status ?? "Unavailable"}</p><p className="mt-1 text-xs text-gray-500">{diagnostic?.utilization_reason ?? "No utilization evidence collected"}</p></div><div className="rounded-lg bg-gray-50 p-4 dark:bg-white/[0.04]"><p className="text-xs font-medium text-gray-500">Security status</p><p className="mt-1 flex items-center gap-1 font-semibold text-gray-900 dark:text-white"><ShieldCheck size={15} className="text-gray-400" />Not resource-scoped</p><p className="mt-1 text-xs text-gray-500">The current evidence provides subscription-level security findings only.</p></div><div className="rounded-lg bg-gray-50 p-4 dark:bg-white/[0.04]"><p className="text-xs font-medium text-gray-500">Potential savings</p><p className="mt-1 font-semibold text-gray-900 dark:text-white">{recommendation?.potential_savings != null ? formatAmount(recommendation!.potential_savings, currency) : "No recommendation"}</p><p className="mt-1 text-xs text-gray-500">{recommendation?.action ?? "No persisted resource recommendation"}</p></div></div><div className="mt-5 grid gap-5 xl:grid-cols-2"><div><h3 className="text-sm font-semibold text-gray-900 dark:text-white">Resource evidence</h3><dl className="mt-3 grid-cols-2 gap-x-4 gap-y-3 text-sm"><div><dt className="text-xs text-gray-500">Type</dt><dd className="mt-1 text-gray-900 dark:text-white">{normalized(selected!.resource_type)}</dd></div><div><dt className="text-xs text-gray-500">Configuration</dt><dd className="mt-1 capitalize text-gray-900 dark:text-white">{selected!.configuration_status}</dd></div><div><dt className="text-xs text-gray-500">Resource group</dt><dd className="mt-1 text-gray-900 dark:text-white">{normalized(selected!.resource_group)}</dd></div><div><dt className="text-xs text-gray-500">Region / SKU</dt><dd className="mt-1 text-gray-900 dark:text-white">{normalized(selected!.location)} / {normalized(selected!.sku)}</dd></div></dl></div><div><h3 className="text-sm font-semibold text-gray-900 dark:text-white">FinOps issues</h3>{missing.length ? <div className="mt-3 flex gap-2 rounded-lg border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200"><AlertTriangle size={17} className="mt-0.5 shrink-0" />Evidence unavailable for: {missing.join(", ")}.</div> : <p className="mt-3 text-sm text-gray-500">No missing evidence was reported for this resource.</p>}<div className="mt-4 flex-wrap gap-3"><Link to="/optimization/waste" className="inline-flex items-center gap-2 rounded-lg border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-white/5">View Issues<ChevronRight size={16} /></Link>{recommendation && <Link to="/optimization/recommendations" className="inline-flex items-center gap-2 rounded-lg bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-600">View Recommendation<ChevronRight size={16} /></Link>}</div></div></div></section>; })()}</div></>;
}
