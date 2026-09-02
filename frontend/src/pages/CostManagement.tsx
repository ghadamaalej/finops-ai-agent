import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Database,
  RefreshCw,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import PageMeta from "../components/common/PageMeta";
import {
  getDashboardSummary,
  type DashboardSummary,
} from "../services/dashboard";

function formatAmount(value: number | null | undefined, currency = "USD") {
  if (value == null) return "No data available";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatCompactAmount(value: number, currency: string) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function metricTone(value: number | null, positiveIsGood = true) {
  if (value == null) return "text-gray-500 dark:text-gray-400";
  return positiveIsGood
    ? value >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"
    : value >= 0 ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400";
}

function KpiCard({ label, value, detail, icon: Icon, tone = "brand" }: {
  label: string;
  value: string;
  detail: string;
  icon: LucideIcon;
  tone?: "brand" | "green" | "orange" | "blue";
}) {
  const tones = {
    brand: "bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-300",
    green: "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-300",
    orange: "bg-orange-50 text-orange-600 dark:bg-orange-500/10 dark:text-orange-300",
    blue: "bg-blue-light-50 text-blue-light-600 dark:bg-blue-light-500/10 dark:text-blue-light-300",
  };
  return (
    <article className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{label}</p>
        <span className={`flex h-9 w-9 items-center justify-center rounded-xl ${tones[tone]}`}><Icon size={17} /></span>
      </div>
      <p className="mt-5 truncate text-2xl font-semibold text-gray-900 dark:text-white">{value}</p>
      <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">{detail}</p>
    </article>
  );
}

function TrendChart({ trend, currency }: { trend: DashboardSummary["cost_overview"]["trend"]; currency: string }) {
  if (!trend.length) return <div className="flex h-72 items-center justify-center rounded-xl border border-dashed border-gray-200 text-sm text-gray-500 dark:border-gray-800">No cost trend data available</div>;
  const width = 760;
  const height = 270;
  const padding = { top: 24, right: 20, bottom: 38, left: 68 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const values = trend.map((item) => item.monthly_cost);
  const max = Math.max(...values, 0);
  const min = Math.min(...values, 0);
  const range = max - min || Math.max(max * 0.1, 1);
  const lower = Math.max(0, min - range * 0.12);
  const upper = max + range * 0.12;
  const scale = upper - lower || 1;
  const points = trend.map((item, index) => ({
    ...item,
    x: padding.left + (trend.length === 1 ? chartWidth / 2 : index / (trend.length - 1) * chartWidth),
    y: padding.top + chartHeight - ((item.monthly_cost - lower) / scale) * chartHeight,
  }));
  const line = points.map((point) => `${point.x},${point.y}`).join(" ");
  const area = `${padding.left},${padding.top + chartHeight} ${line} ${padding.left + chartWidth},${padding.top + chartHeight}`;
  const date = (timestamp: string) => new Date(timestamp).toLocaleDateString("en-US", { month: "short", day: "numeric" });

  return (
    <div className="rounded-xl border border-gray-100 bg-gray-50/70 p-2 dark:border-gray-800 dark:bg-white/[0.02] sm:p-4">
      <svg className="h-72 w-full overflow-visible" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" role="img" aria-label="Cost trend">
        <defs><linearGradient id="cost-management-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" className="text-brand-500" stopColor="currentColor" stopOpacity=".22" /><stop offset="100%" className="text-brand-500" stopColor="currentColor" stopOpacity="0" /></linearGradient></defs>
        {[0, 0.5, 1].map((position) => {
          const y = padding.top + chartHeight * position;
          return <g key={position}><line x1={padding.left} x2={padding.left + chartWidth} y1={y} y2={y} className="stroke-gray-200 dark:stroke-gray-700" strokeDasharray="3 5" /><text x={padding.left - 12} y={y + 4} textAnchor="end" className="fill-gray-400 text-[11px]">{formatCompactAmount(upper - scale * position, currency)}</text></g>;
        })}
        <polygon points={area} fill="url(#cost-management-fill)" />
        <polyline points={line} fill="none" className="stroke-brand-500" strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" vectorEffect="non-scaling-stroke" />
        {points.map((point) => <circle key={`${point.timestamp}-${point.monthly_cost}`} cx={point.x} cy={point.y} r="4" className="fill-white stroke-brand-500 dark:fill-gray-900" strokeWidth="2" vectorEffect="non-scaling-stroke"><title>{`${date(point.timestamp)}: ${formatAmount(point.monthly_cost, currency)}`}</title></circle>)}
        <text x={padding.left} y={height - 8} className="fill-gray-400 text-[11px]">{date(trend[0].timestamp)}</text>
        <text x={padding.left + chartWidth} y={height - 8} textAnchor="end" className="fill-gray-400 text-[11px]">{date(trend[trend.length - 1].timestamp)}</text>
      </svg>
    </div>
  );
}

type CostResource = DashboardSummary["cost_by_resource"][number];
type Granularity = "daily" | "weekly" | "monthly";
type ResourceScope = "top5" | "top10" | "all";
type TableView = "all" | "top5" | "top10" | "highest" | "lowest";

function periodKey(timestamp: string, granularity: Granularity) {
  const date = new Date(timestamp);
  if (granularity === "monthly") return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, "0")}`;
  if (granularity === "weekly") {
    const start = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
    start.setUTCDate(start.getUTCDate() - start.getUTCDay());
    return start.toISOString().slice(0, 10);
  }
  return date.toISOString().slice(0, 10);
}

export function LegacyResourceTrendChart({ series, currency, granularity }: { series: Array<{ resource: CostResource; points: Array<{ timestamp: string; monthly_cost: number }> }>; currency: string; granularity: Granularity }) {
  const buckets = [...new Set(series.flatMap((item) => item.points.map((point) => periodKey(point.timestamp, granularity))))].sort();
  if (!buckets.length) return <div className="flex h-80 items-center justify-center rounded-xl border border-dashed border-gray-200 text-sm text-gray-500 dark:border-gray-800">No resource cost history matches the selected controls.</div>;
  const width = 820;
  const height = 300;
  const padding = { top: 22, right: 24, bottom: 42, left: 72 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const values = series.flatMap((item) => buckets.map((bucket) => item.points.filter((point) => periodKey(point.timestamp, granularity) === bucket).reduce((total, point) => total + point.monthly_cost, 0)));
  const max = Math.max(...values, 0);
  const scale = max || 1;
  const colors = ["#0078d4", "#107c10", "#ca5010", "#8764b8", "#038387", "#d13438"];
  const formatBucket = (bucket: string) => {
    const value = granularity === "monthly" ? `${bucket}-01` : bucket;
    const date = new Date(`${value}T00:00:00Z`);
    return Number.isNaN(date.getTime()) ? "Date unavailable" : date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: granularity === "monthly" ? "numeric" : undefined });
  };
  return <div className="space-y-4"><div className="overflow-x-auto rounded-xl border border-gray-100 bg-gray-50/70 p-2 dark:border-gray-800 dark:bg-white/[0.02] sm:p-4"><svg className="h-80 min-w-[620px] w-full overflow-visible" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" role="img" aria-label="Cost by resource over time">{[0, 0.5, 1].map((position) => { const y = padding.top + chartHeight * position; return <g key={position}><line x1={padding.left} x2={padding.left + chartWidth} y1={y} y2={y} className="stroke-gray-200 dark:stroke-gray-700" strokeDasharray="3 5" /><text x={padding.left - 12} y={y + 4} textAnchor="end" className="fill-gray-400 text-[11px]">{formatCompactAmount(max * (1 - position), currency)}</text></g>; })}{series.map((item, seriesIndex) => { const points = buckets.map((bucket, index) => ({ bucket, value: item.points.filter((point) => periodKey(point.timestamp, granularity) === bucket).reduce((total, point) => total + point.monthly_cost, 0), x: padding.left + (buckets.length === 1 ? chartWidth / 2 : index / (buckets.length - 1) * chartWidth) })); const line = points.map((point) => `${point.x},${padding.top + chartHeight - point.value / scale * chartHeight}`).join(" "); return <g key={item.resource.resource_id}><polyline points={line} fill="none" stroke={colors[seriesIndex % colors.length]} strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" vectorEffect="non-scaling-stroke" />{points.map((point) => <circle key={point.bucket} cx={point.x} cy={padding.top + chartHeight - point.value / scale * chartHeight} r="4" fill={colors[seriesIndex % colors.length]} stroke="white" strokeWidth="2" vectorEffect="non-scaling-stroke"><title>{`${item.resource.resource_name ?? item.resource.resource_id} · ${formatBucket(point.bucket)}: ${formatAmount(point.value, currency)}`}</title></circle>)}</g>; })}<text x={padding.left} y={height - 10} className="fill-gray-400 text-[11px]">{formatBucket(buckets[0])}</text><text x={padding.left + chartWidth} y={height - 10} textAnchor="end" className="fill-gray-400 text-[11px]">{formatBucket(buckets[buckets.length - 1])}</text></svg></div><div className="flex flex-wrap gap-x-5 gap-y-2">{series.map((item, index) => <span key={item.resource.resource_id} className="inline-flex max-w-full items-center gap-2 text-xs text-gray-600 dark:text-gray-300"><span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: colors[index % colors.length] }} /><span className="truncate">{item.resource.resource_name ?? item.resource.resource_id}</span></span>)}</div></div>;
}

function ResourceBarChart({ series, currency, granularity }: { series: Array<{ resource: CostResource; points: Array<{ timestamp: string; monthly_cost: number }> }>; currency: string; granularity: Granularity }) {
  const totals = series.map((item) => ({
    resource: item.resource,
    monthlyCost: item.points.reduce((total, point) => total + point.monthly_cost, 0),
  })).sort((left, right) => right.monthlyCost - left.monthlyCost);
  if (!totals.length) return <div className="flex h-80 items-center justify-center rounded-xl border border-dashed border-gray-200 text-sm text-gray-500 dark:border-gray-800">No resource cost history matches the selected controls.</div>;

  const width = Math.max(760, totals.length * 92);
  const height = 320;
  const padding = { top: 24, right: 24, bottom: 76, left: 76 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const max = Math.max(...totals.map((item) => item.monthlyCost), 0);
  const scale = max || 1;
  const barSlot = chartWidth / totals.length;
  const barWidth = Math.min(52, barSlot * 0.62);
  const color = "#0078d4";
  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    return Number.isNaN(date.getTime()) ? "Date unavailable" : date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  };
  const rangeLabel = series.flatMap((item) => item.points).sort((a, b) => a.timestamp.localeCompare(b.timestamp));
  const subtitle = rangeLabel.length ? `${formatDate(rangeLabel[0].timestamp)} - ${formatDate(rangeLabel[rangeLabel.length - 1].timestamp)} · ${granularity}` : "No date range available";

  return <div className="space-y-4">
    <div className="overflow-x-auto rounded-xl border border-gray-100 bg-gray-50/70 p-2 dark:border-gray-800 dark:bg-white/[0.02] sm:p-4">
      <svg className="h-80 w-full min-w-[760px]" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Monthly cost by resource vertical bar chart">
        {[0, 0.5, 1].map((position) => { const y = padding.top + chartHeight * position; return <g key={position}><line x1={padding.left} x2={width - padding.right} y1={y} y2={y} className="stroke-gray-200 dark:stroke-gray-700" strokeDasharray="3 5" /><text x={padding.left - 12} y={y + 4} textAnchor="end" className="fill-gray-400 text-[11px]">{formatCompactAmount(max * (1 - position), currency)}</text></g>; })}
        <line x1={padding.left} x2={width - padding.right} y1={padding.top + chartHeight} y2={padding.top + chartHeight} className="stroke-gray-300 dark:stroke-gray-600" />
        {totals.map((item, index) => { const barHeight = item.monthlyCost / scale * chartHeight; const x = padding.left + index * barSlot + (barSlot - barWidth) / 2; const y = padding.top + chartHeight - barHeight; const label = item.resource.resource_name ?? item.resource.resource_id; return <g key={item.resource.resource_id}><rect x={x} y={y} width={barWidth} height={Math.max(barHeight, 1)} rx="4" fill={color} className="transition-opacity hover:opacity-80"><title>{`${label}: ${formatAmount(item.monthlyCost, currency)}`}</title></rect><text x={x + barWidth / 2} y={height - 42} textAnchor="middle" className="fill-gray-600 text-[11px] dark:fill-gray-300"><title>{label}</title>{label.length > 14 ? `${label.slice(0, 12)}…` : label}</text></g>; })}
      </svg>
    </div>
    <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-gray-500 dark:text-gray-400"><span>{subtitle}</span><span className="inline-flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: color }} />Monthly cost</span></div>
  </div>;
}

export default function CostManagement() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [granularity, setGranularity] = useState<Granularity>("monthly");
  const [resourceFilter, setResourceFilter] = useState("all");
  const [serviceFilter, setServiceFilter] = useState("all");
  const [resourceGroupFilter, setResourceGroupFilter] = useState("all");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [resourceScope, setResourceScope] = useState<ResourceScope>("top5");
  const [tableSearch, setTableSearch] = useState("");
  const [tablePage, setTablePage] = useState(1);
  const [tableView, setTableView] = useState<TableView>("all");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setSummary(await getDashboardSummary());
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load cost data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const currency = summary?.cost.currency ?? "USD";
  const resources = useMemo(() => summary?.cost_by_resource ?? [], [summary]);
  const tableResources = useMemo(() => summary?.cost_resources ?? [], [summary]);
  const resourceGroups = useMemo(() => [...new Set(resources.map((item) => item.resource_group ?? "Unclassified"))].sort(), [resources]);
  const services = useMemo(() => [...new Set(resources.map((item) => item.service_name ?? "Unclassified"))].sort(), [resources]);
  const resourceOptions = useMemo(() => resources.slice().sort((a, b) => (a.resource_name ?? a.resource_id).localeCompare(b.resource_name ?? b.resource_id)), [resources]);
  const filteredResourceSeries = useMemo(() => resources.filter((item) => {
    const matchesResource = resourceFilter === "all" || item.resource_id === resourceFilter;
    const matchesGroup = resourceGroupFilter === "all" || item.resource_group === resourceGroupFilter;
    const matchesService = serviceFilter === "all" || (item.service_name ?? "Unclassified") === serviceFilter;
    return matchesResource && matchesGroup && matchesService;
  }).sort((a, b) => b.points.reduce((total, point) => total + point.monthly_cost, 0) - a.points.reduce((total, point) => total + point.monthly_cost, 0)).slice(0, resourceFilter !== "all" ? undefined : resourceScope === "top5" ? 5 : resourceScope === "top10" ? 10 : undefined).map((resource) => ({
    resource,
    points: resource.points.filter((point) => (!startDate || point.timestamp >= `${startDate}T00:00:00Z`) && (!endDate || point.timestamp <= `${endDate}T23:59:59Z`)),
  })), [endDate, resourceFilter, resourceGroupFilter, resources, resourceScope, serviceFilter, startDate]);
  const filteredTrend = summary?.cost_overview.trend ?? [];
  const filteredTableResources = useMemo(() => tableResources.filter((item) => {
    const query = tableSearch.trim().toLowerCase();
    const matchesSearch = !query || [item.resource_name, item.resource_id, item.resource_type, item.service_name, item.resource_group].some((value) => value?.toLowerCase().includes(query));
    const matchesGroup = resourceGroupFilter === "all" || item.resource_group === resourceGroupFilter;
    const matchesService = serviceFilter === "all" || (item.service_name ?? item.resource_type ?? "Unclassified") === serviceFilter;
    return matchesSearch && matchesGroup && matchesService;
  }), [resourceGroupFilter, serviceFilter, tableResources, tableSearch]);
  const tableViewResources = useMemo(() => {
    if (tableView === "highest") return filteredTableResources.slice(0, 1);
    if (tableView === "lowest") return filteredTableResources.slice(-1);
    if (tableView === "top5") return filteredTableResources.slice(0, 5);
    if (tableView === "top10") return filteredTableResources.slice(0, 10);
    return filteredTableResources;
  }, [filteredTableResources, tableView]);
  const tablePageCount = Math.max(1, Math.ceil(tableViewResources.length / 10));
  const pagedTableResources = tableViewResources.slice((tablePage - 1) * 10, tablePage * 10);
  useEffect(() => { setTablePage(1); }, [resourceGroupFilter, serviceFilter, tableSearch, tableView]);
  const recommendations = useMemo(() => new Map((summary?.recommendations ?? []).map((item) => [item.resource_id.toLowerCase(), item])), [summary]);
  if (loading && !summary) return <div className="p-8 text-sm text-gray-500">Loading Azure cost data…</div>;
  if (error && !summary) return <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">{error}</div>;
  if (!summary) return null;

  const change = summary?.cost.change_percent ?? null;
  const dailyAverage = summary?.cost.monthly == null ? null : summary.cost.monthly / 30;

  return (
    <>
      <PageMeta title="FinOps Agent · Cost Management" description="Azure FinOps cost management dashboard" />
      <div className="space-y-6">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-brand-500">COST MANAGEMENT</p>
            <h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">Azure cost overview</h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">A focused view of spend, trend and the resources driving it.</p>
          </div>
          <button type="button" onClick={() => void load()} disabled={loading} className="inline-flex items-center gap-2 rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-600 disabled:cursor-not-allowed disabled:opacity-60"><RefreshCw size={16} className={loading ? "animate-spin" : ""} />{loading ? "Refreshing" : "Refresh data"}</button>
        </header>

        {error && <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-300">Showing the last successful result. Refresh failed: {error}</div>}

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            <KpiCard label="Monthly cost" value={formatAmount(summary.cost.monthly, currency)} detail={summary.cost.is_estimated ? "Estimated · Azure Retail Prices" : "Actual cost evidence"} icon={Database} tone="brand" />
            <KpiCard label="Previous month" value={formatAmount(summary.cost.previous, currency)} detail="Previous persisted cost snapshot" icon={ArrowDownRight} tone="blue" />
            <KpiCard label="Cost change" value={change == null ? "No data available" : `${change >= 0 ? "+" : ""}${change.toFixed(1)}%`} detail="Compared with previous snapshot" icon={change != null && change >= 0 ? ArrowUpRight : ArrowDownRight} tone={change != null && change >= 0 ? "orange" : "green"} />
            <KpiCard label="Daily average" value={formatAmount(dailyAverage, currency)} detail="Monthly cost divided by 30 days" icon={BarChart3} tone="green" />
            <KpiCard label="Forecast" value={formatAmount(summary.cost.forecast, currency)} detail="Projected next period" icon={TrendingUp} tone="blue" />
          </div>

          <div className="grid gap-6 xl:grid-cols-5">
            <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm xl:col-span-3 dark:border-gray-800 dark:bg-white/[0.03]"><div className="mb-5 flex items-start justify-between gap-4"><div><h2 className="font-semibold text-gray-900 dark:text-white">Cost trend</h2><p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Persisted Azure cost snapshots for the selected period.</p></div><span className={`text-sm font-semibold ${metricTone(change)}`}>{change == null ? "No change data" : `${change >= 0 ? "Up" : "Down"} ${Math.abs(change).toFixed(1)}%`}</span></div><TrendChart trend={filteredTrend} currency={currency} /></section>
            <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm xl:col-span-2 dark:border-gray-800 dark:bg-white/[0.03]"><div className="mb-5 flex items-start justify-between gap-3"><div><h2 className="font-semibold text-gray-900 dark:text-white">Cost by service</h2><p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Share of current monthly spend.</p></div><BarChart3 size={18} className="text-brand-500" /></div>{summary.cost_composition.length ? <div className="space-y-4">{summary.cost_composition.slice(0, 6).map((item) => { const share = summary.cost.monthly && summary.cost.monthly > 0 ? item.monthly_cost / summary.cost.monthly * 100 : 0; return <div key={item.name}><div className="flex justify-between gap-3 text-sm"><span className="truncate font-medium text-gray-700 dark:text-gray-300">{item.name}</span><span className="shrink-0 font-semibold text-gray-900 dark:text-white">{formatAmount(item.monthly_cost, currency)}</span></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-gray-100 dark:bg-white/10"><div className="h-full rounded-full bg-brand-500" style={{ width: `${Math.min(share, 100)}%` }} /></div><p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{share.toFixed(1)}% of total</p></div>; })}</div> : <p className="text-sm text-gray-500">No service cost data available.</p>}</section>
          </div>

          <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
            <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
              <div><h2 className="font-semibold text-gray-900 dark:text-white">Cost by Resource</h2><p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Compare persisted resource spend across time.</p></div>
              <div className="flex rounded-lg border border-gray-200 p-1 dark:border-gray-700" aria-label="Chart granularity">
                {(["daily", "weekly", "monthly"] as Granularity[]).map((value) => <button key={value} type="button" onClick={() => setGranularity(value)} className={`rounded-md px-3 py-1.5 text-xs font-semibold capitalize ${granularity === value ? "bg-brand-500 text-white" : "text-gray-500 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-white/5"}`}>{value}</button>)}
              </div>
            </div>
            <div className="mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
              <label className="text-xs font-medium text-gray-500">Date from<input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} className="mt-1 block w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-white" /></label>
              <label className="text-xs font-medium text-gray-500">Date to<input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} className="mt-1 block w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-white" /></label>
              <label className="text-xs font-medium text-gray-500">Resource<select value={resourceFilter} onChange={(event) => setResourceFilter(event.target.value)} className="mt-1 block w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-white"><option value="all">All resources</option>{resourceOptions.map((item) => <option key={item.resource_id} value={item.resource_id}>{item.resource_name ?? item.resource_id}</option>)}</select></label>
              <label className="text-xs font-medium text-gray-500">Service<select value={serviceFilter} onChange={(event) => setServiceFilter(event.target.value)} className="mt-1 block w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-white"><option value="all">All services</option>{services.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
              <label className="text-xs font-medium text-gray-500">Resource group<select value={resourceGroupFilter} onChange={(event) => setResourceGroupFilter(event.target.value)} className="mt-1 block w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-white"><option value="all">All groups</option>{resourceGroups.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
              <label className="text-xs font-medium text-gray-500">Series<select value={resourceScope} onChange={(event) => setResourceScope(event.target.value as ResourceScope)} className="mt-1 block w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-white"><option value="top5">Top 5 resources</option><option value="top10">Top 10 resources</option><option value="all">All resources</option></select></label>
            </div>
            <ResourceBarChart series={filteredResourceSeries} currency={currency} granularity={granularity} />
          </section>

          <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]"><div className="mb-5 flex flex-wrap items-end justify-between gap-3"><div><h2 className="text-lg font-semibold text-gray-900 dark:text-white">Resources &amp; Costs</h2><p className="mt-1 text-sm text-gray-500 dark:text-gray-400">All positive-cost resources in the selected subscription.</p></div><span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-600 dark:bg-brand-500/10 dark:text-brand-300">{tableViewResources.length} resources</span></div><div className="mb-4 flex flex-wrap gap-3"><input type="search" value={tableSearch} onChange={(event) => setTableSearch(event.target.value)} placeholder="Search resources, services or groups" className="min-w-[240px] flex-1 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-brand-500 dark:border-gray-700 dark:bg-gray-900 dark:text-white" /><select value={tableView} onChange={(event) => setTableView(event.target.value as TableView)} className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-white"><option value="all">All resources</option><option value="top5">Top 5</option><option value="top10">Top 10</option><option value="highest">Highest cost</option><option value="lowest">Lowest cost</option></select></div><div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm"><thead className="border-b border-gray-200 text-xs uppercase tracking-wider text-gray-500 dark:border-gray-800"><tr><th className="pb-3 pr-4">Resource</th><th className="pb-3 pr-4">Resource type</th><th className="pb-3 pr-4">Service</th><th className="pb-3 pr-4">Monthly cost</th><th className="pb-3 pr-4">% of total</th><th className="pb-3">Optimization</th></tr></thead><tbody>{pagedTableResources.length ? pagedTableResources.map((item) => { const recommendation = recommendations.get(item.resource_id.toLowerCase()); return <tr key={item.resource_id} className="border-b border-gray-50 last:border-0 dark:border-gray-800/60"><td className="max-w-[250px] py-4 pr-4"><p className="truncate font-semibold text-gray-900 dark:text-white">{item.resource_name ?? item.resource_id}</p><p className="mt-0.5 truncate text-xs text-gray-500 dark:text-gray-400">{item.resource_group ?? "Resource group unavailable"}</p></td><td className="py-4 pr-4 text-gray-600 dark:text-gray-300">{item.resource_type ?? "Resource type unavailable"}</td><td className="py-4 pr-4 text-gray-600 dark:text-gray-300">{item.service_name ?? "Service unavailable"}</td><td className="py-4 pr-4 font-semibold text-gray-900 dark:text-white">{formatAmount(item.monthly_cost, currency)}</td><td className="py-4 pr-4 font-medium text-gray-700 dark:text-gray-300">{item.percent_of_total == null ? "No data available" : `${item.percent_of_total.toFixed(1)}%`}</td><td className="py-4">{recommendation ? <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">{formatAmount(recommendation.potential_savings, currency)} potential</span> : <span className="text-xs text-gray-400">No recommendation</span>}</td></tr>; }) : <tr><td colSpan={6} className="py-10 text-center text-sm text-gray-500">No resources match the selected filters.</td></tr>}</tbody></table></div><div className="mt-4 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400"><span>Page {tablePage} of {tablePageCount}</span><div className="flex gap-2"><button type="button" onClick={() => setTablePage((page) => Math.max(1, page - 1))} disabled={tablePage === 1} className="rounded-lg border border-gray-200 px-3 py-1.5 disabled:opacity-40 dark:border-gray-700">Previous</button><button type="button" onClick={() => setTablePage((page) => Math.min(tablePageCount, page + 1))} disabled={tablePage === tablePageCount} className="rounded-lg border border-gray-200 px-3 py-1.5 disabled:opacity-40 dark:border-gray-700">Next</button></div></div></section>
      </div>
    </>
  );
}
