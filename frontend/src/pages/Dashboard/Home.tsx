import { useCallback, useEffect, useState } from "react";
import { useMsal } from "@azure/msal-react";
import { Link } from "react-router";
import PageMeta from "../../components/common/PageMeta";
import {
  getDashboardSummary,
  refreshDashboardCosts,
  type DashboardSummary,
} from "../../services/dashboard";
import { getAzureManagementAccessToken } from "../../lib/entra";

/* -------------------------------------------------------------------------- */
/* Helpers                                                                    */
/* -------------------------------------------------------------------------- */

function amount(
  value: number | null | undefined,
  currency = "USD"
) {
  return value == null
    ? "No data available"
    : new Intl.NumberFormat("en-US", {
        style: "currency",
        currency,
        maximumFractionDigits: 2,
      }).format(value);
}

function count(value: number | null | undefined) {
  return value == null ? "No data available" : String(value);
}

/* -------------------------------------------------------------------------- */
/* Generic UI                                                                 */
/* -------------------------------------------------------------------------- */

function Card({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <article className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md dark:border-gray-800 dark:bg-white/[0.03]">
      <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
        {label}
      </p>

      <p className="mt-4 text-2xl font-semibold text-gray-900 dark:text-white">
        {value}
      </p>

      <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
        {detail}
      </p>
    </article>
  );
}

function Title({
  children,
  to,
  label,
}: {
  children: string;
  to?: string;
  label?: string;
}) {
  return (
    <div className="mb-5 flex items-center justify-between gap-4">
      <h2 className="font-semibold text-gray-900 dark:text-white">
        {children}
      </h2>

      {to && (
        <Link
          className="whitespace-nowrap text-sm font-medium text-brand-500 transition hover:text-brand-600"
          to={to}
        >
          {label ?? "View all"} →
        </Link>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Cost Trend Chart                                                           */
/* -------------------------------------------------------------------------- */

function CostTrendChart({
  trend,
  currency,
}: {
  trend: DashboardSummary["cost_overview"]["trend"];
  currency: string;
}) {
  if (!trend.length) {
    return (
      <div className="flex h-52 items-center justify-center rounded-xl bg-gray-50 text-sm text-gray-500 dark:bg-white/5">
        No persisted cost trend available
      </div>
    );
  }

  const width = 720;
  const height = 240;

  const padding = {
    top: 18,
    right: 18,
    bottom: 34,
    left: 54,
  };

  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const values = trend.map((point) => point.monthly_cost);

  const minimum = Math.min(...values);
  const maximum = Math.max(...values);

  const range =
    maximum - minimum || Math.max(Math.abs(maximum) * 0.1, 1);

  const lowerBound = Math.max(0, minimum - range * 0.12);
  const upperBound = maximum + range * 0.12;

  const scale = upperBound - lowerBound || 1;

  const points = trend.map((point, index) => ({
    ...point,
    x:
      padding.left +
      (trend.length === 1
        ? chartWidth / 2
        : (index / (trend.length - 1)) * chartWidth),
    y:
      padding.top +
      chartHeight -
      ((point.monthly_cost - lowerBound) / scale) * chartHeight,
  }));

  const line = points
    .map((point) => `${point.x},${point.y}`)
    .join(" ");

  const area = `${padding.left},${
    padding.top + chartHeight
  } ${line} ${padding.left + chartWidth},${
    padding.top + chartHeight
  }`;

  const gridLines = [0, 0.5, 1];

  const formatDate = (timestamp: string) =>
    new Date(timestamp).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });

  return (
    <div className="rounded-2xl border border-gray-100 bg-gray-50/80 p-3 dark:border-gray-800 dark:bg-white/[0.03] sm:p-4">
      <svg
        className="h-52 w-full overflow-visible"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        role="img"
        aria-label="Monthly cost trend chart"
      >
        <defs>
          <linearGradient
            id="cost-trend-fill"
            x1="0"
            x2="0"
            y1="0"
            y2="1"
          >
            <stop
              offset="0%"
              className="text-brand-500"
              stopColor="currentColor"
              stopOpacity="0.22"
            />
            <stop
              offset="100%"
              className="text-brand-500"
              stopColor="currentColor"
              stopOpacity="0"
            />
          </linearGradient>
        </defs>

        {gridLines.map((position) => {
          const y = padding.top + chartHeight * position;

          return (
            <g key={position}>
              <line
                x1={padding.left}
                x2={padding.left + chartWidth}
                y1={y}
                y2={y}
                className="stroke-gray-200 dark:stroke-gray-700"
                strokeDasharray="3 5"
              />

              <text
                x={padding.left - 10}
                y={y + 4}
                textAnchor="end"
                className="fill-gray-400 text-[11px]"
              >
                {amount(
                  upperBound - scale * position,
                  currency
                )}
              </text>
            </g>
          );
        })}

        <polygon
          points={area}
          fill="url(#cost-trend-fill)"
        />

        <polyline
          points={line}
          fill="none"
          className="stroke-brand-500"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="3"
          vectorEffect="non-scaling-stroke"
        />

        {points.map((point) => (
          <circle
            key={`${point.timestamp}-${point.monthly_cost}`}
            cx={point.x}
            cy={point.y}
            r="4"
            className="fill-white stroke-brand-500 dark:fill-gray-900"
            strokeWidth="2"
            vectorEffect="non-scaling-stroke"
          >
            <title>
              {`${formatDate(point.timestamp)}: ${amount(
                point.monthly_cost,
                currency
              )}`}
            </title>
          </circle>
        ))}

        <text
          x={padding.left}
          y={height - 8}
          className="fill-gray-400 text-[11px]"
        >
          {formatDate(trend[0].timestamp)}
        </text>

        <text
          x={padding.left + chartWidth}
          y={height - 8}
          textAnchor="end"
          className="fill-gray-400 text-[11px]"
        >
          {formatDate(trend[trend.length - 1].timestamp)}
        </text>
      </svg>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Cost Composition                                                           */
/* -------------------------------------------------------------------------- */

function CostComposition({
  items,
  monthlyCost,
  currency,
}: {
  items: DashboardSummary["cost_composition"];
  monthlyCost: number | null | undefined;
  currency: string;
}) {
  if (!items.length) {
    return (
      <div className="flex h-52 items-center justify-center rounded-xl border border-dashed border-gray-200 text-sm text-gray-500 dark:border-gray-800">
        No cost composition data available
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {items.filter((item) => item.monthly_cost > 0).map((item, index) => {
        const percentage =
          monthlyCost && monthlyCost > 0
            ? Math.min(
                (item.monthly_cost / monthlyCost) * 100,
                100
              )
            : 0;

        const icon =
          item.name.toLowerCase().includes("virtual")
            ? "🖥️"
            : item.name.toLowerCase().includes("disk")
            ? "💾"
            : "☁️";

        return (
          <div
            key={`${item.name}-${index}`}
            className="rounded-xl border border-gray-100 bg-gray-50/70 p-4 transition-all hover:border-brand-200 hover:bg-brand-50/40 dark:border-gray-800 dark:bg-white/[0.02] dark:hover:border-brand-500/30 dark:hover:bg-brand-500/5"
          >
            <div className="flex items-center justify-between gap-4">
              <div className="flex min-w-0 items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white text-lg shadow-sm dark:bg-white/10">
                  {icon}
                </div>

                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-gray-900 dark:text-white">
                    {item.name}
                  </p>

                  <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                    {percentage.toFixed(1)}% of total spend
                  </p>
                </div>
              </div>

              <p className="shrink-0 text-sm font-bold text-gray-900 dark:text-white">
                {amount(item.monthly_cost, currency)}
              </p>
            </div>

            <div className="mt-4 h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-white/10">
              <div
                className="h-full rounded-full bg-brand-500 transition-all duration-500"
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function CostDrivers({
  items,
  currency,
}: {
  items: DashboardSummary["cost_drivers"];
  currency: string;
}) {
  if (!items.length) {
    return (
      <div className="rounded-xl border border-dashed border-gray-200 p-8 text-center text-sm text-gray-500 dark:border-gray-800">
        No cost drivers available
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[700px] text-left">
        <thead>
          <tr className="border-b border-gray-100 dark:border-gray-800">
            <th className="w-12 pb-3 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
              #
            </th>

            <th className="pb-3 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Resource
            </th>

            <th className="pb-3 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Type
            </th>

            <th className="pb-3 text-right text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Monthly cost
            </th>

            <th className="pb-3 text-right text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
              % of total
            </th>
          </tr>
        </thead>

        <tbody>
          {items.map((item, index) => (
            <tr
              key={`${item.resource_id}-${index}`}
              className="border-b border-gray-50 last:border-0 transition-colors hover:bg-gray-50/70 dark:border-gray-800/60 dark:hover:bg-white/[0.02]"
            >
              {/* Rank */}
              <td className="py-4">
                <span
                  className={`flex h-7 w-7 items-center justify-center rounded-lg text-xs font-semibold ${
                    index === 0
                      ? "bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-300"
                      : "bg-gray-100 text-gray-500 dark:bg-white/10 dark:text-gray-400"
                  }`}
                >
                  {index + 1}
                </span>
              </td>

              {/* Resource */}
              <td className="py-4 pr-4">
                <div className="flex items-center gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-gray-900 dark:text-white">
                      {item.resource_name ?? item.resource_id}
                    </p>

                    {index === 0 && (
                      <span className="text-[10px] font-medium uppercase tracking-wide text-brand-500">
                        Highest cost resource
                      </span>
                    )}
                  </div>
                </div>
              </td>

              {/* Type */}
              <td className="py-4 pr-4">
                <span className="text-sm text-gray-600 dark:text-gray-300">
                  {item.resource_type ?? "Resource type unavailable"}
                </span>
              </td>

              {/* Monthly cost */}
              <td className="py-4 text-right">
                <span className="text-sm font-bold text-gray-900 dark:text-white">
                  {amount(item.monthly_cost, currency)}
                </span>
              </td>

              {/* Percentage */}
              <td className="py-4 text-right">
                <span className="text-sm font-bold text-gray-900 dark:text-white">
                  {item.percent_of_total == null
                    ? "No data available"
                    : `${item.percent_of_total.toFixed(1)}%`}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
/* -------------------------------------------------------------------------- */
/* Optimization Opportunities                                                 */
/* -------------------------------------------------------------------------- */

function OptimizationOpportunities({
  opportunities,
  potentialSavings,
  currency,
}: {
  opportunities: DashboardSummary["optimization_opportunities"];
  potentialSavings: number | null | undefined;
  currency: string;
}) {
  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
      <Title to="/recommendations">
        Optimization opportunities
      </Title>

      <div className="mb-5 rounded-xl bg-gradient-to-r from-emerald-50 to-green-50 p-4 dark:from-emerald-500/10 dark:to-green-500/5">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-emerald-600 dark:text-emerald-400">
              Potential savings
            </p>

            <p className="mt-1 text-2xl font-bold text-emerald-700 dark:text-emerald-300">
              {amount(potentialSavings, currency)}
            </p>

            <p className="mt-1 text-xs text-emerald-600/80 dark:text-emerald-400/80">
              Estimated monthly savings
            </p>
          </div>

          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-xl dark:bg-emerald-500/20">
            💰
          </div>
        </div>
      </div>

      {opportunities.length ? (
        <div className="space-y-3">
          {opportunities.map((item, index) => (
            <div
              key={`${item.category}-${index}`}
              className="flex items-center justify-between rounded-xl border border-gray-100 p-4 transition-all hover:border-brand-200 hover:bg-gray-50 dark:border-gray-800 dark:hover:border-brand-500/30 dark:hover:bg-white/[0.03]"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-300">
                  ✦
                </div>

                <div>
                  <p className="text-sm font-semibold text-gray-900 dark:text-white">
                    {item.category}
                  </p>

                  <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                    {item.count} recommendation
                    {item.count !== 1 ? "s" : ""}
                  </p>
                </div>
              </div>

              <p className="text-sm font-bold text-emerald-600 dark:text-emerald-400">
                {amount(item.potential_savings, currency)}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-gray-500">
          No optimization opportunities available.
        </p>
      )}
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/* AI Recommendations                                                         */
/* -------------------------------------------------------------------------- */

function Recommendations({
  recommendations,
  currency,
}: {
  recommendations: DashboardSummary["recommendations"];
  currency: string;
}) {
  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
      <Title
        to="/recommendations"
        label="View all recommendations"
      >
        AI FinOps recommendations
      </Title>

      {recommendations.length ? (
        <div className="grid gap-4 md:grid-cols-3">
          {recommendations.map((item, index) => {
            const confidence =
              item.confidence == null
                ? null
                : Math.round(item.confidence * 100);

            return (
              <article
                key={`${item.recommendation_id}-${item.resource_id}-${index}`}
                className="group rounded-2xl border border-gray-200 bg-white p-4 transition-all duration-200 hover:-translate-y-1 hover:border-brand-200 hover:shadow-lg dark:border-gray-800 dark:bg-white/[0.02] dark:hover:border-brand-500/30"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-300">
                    ⚡
                  </div>

                  <span
                    className={`rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide ${
                      item.approved
                        ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300"
                        : "bg-yellow-100 text-yellow-700 dark:bg-yellow-500/15 dark:text-yellow-300"
                    }`}
                  >
                    {item.approved ? "Approved" : "Pending"}
                  </span>
                </div>

                <p className="mt-4 text-[11px] font-semibold uppercase tracking-wider text-brand-500">
                  {item.action ?? "Recommendation"}
                </p>

                <h3 className="mt-1 truncate text-base font-semibold text-gray-900 dark:text-white">
                  {item.resource_name ?? item.resource_id}
                </h3>

                <div className="mt-4 rounded-xl bg-emerald-50 p-3 dark:bg-emerald-500/10">
                  <p className="text-xs text-emerald-600 dark:text-emerald-400">
                    Potential savings
                  </p>

                  <p className="mt-1 text-lg font-bold text-emerald-700 dark:text-emerald-300">
                    {amount(item.potential_savings, currency)}
                    <span className="ml-1 text-xs font-medium">
                      /month
                    </span>
                  </p>
                </div>

                <div className="mt-4">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">
                      AI confidence
                    </span>

                    <span className="font-semibold text-gray-700 dark:text-gray-300">
                      {confidence == null ? "No data" : `${confidence}%`}
                    </span>
                  </div>

                  {confidence != null && (
                    <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-gray-100 dark:bg-white/10">
                      <div
                        className="h-full rounded-full bg-brand-500"
                        style={{
                          width: `${confidence}%`,
                        }}
                      />
                    </div>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-gray-200 p-8 text-center dark:border-gray-800">
          <div className="text-2xl">🤖</div>

          <p className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
            No recommendations available
          </p>

          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            The FinOps agent has not identified any new optimization
            opportunities.
          </p>
        </div>
      )}
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/* Environment Monitoring                                                     */
/* -------------------------------------------------------------------------- */

function EnvironmentMonitoring({
  summary,
}: {
  summary: DashboardSummary;
}) {
  const monitoring = [
    {
      key: "security",
      label: "Security",
      icon: "🛡️",
      score: summary.security.score,
      suffix: "/100",
      detail: `${count(summary.security.critical)} critical · ${count(
        summary.security.high
      )} high`,
      color:
        "text-red-600 dark:text-red-400",
      bg:
        "bg-red-50 dark:bg-red-500/10",
      border:
        "border-red-100 dark:border-red-500/20",
    },
    {
      key: "governance",
      label: "Governance",
      icon: "📋",
      score: summary.governance.compliance,
      suffix: "%",
      detail: `${count(summary.governance.violations)} violations · ${count(
        summary.governance.affected_resources
      )} affected`,
      color:
        "text-blue-600 dark:text-blue-400",
      bg:
        "bg-blue-50 dark:bg-blue-500/10",
      border:
        "border-blue-100 dark:border-blue-500/20",
    },
    {
      key: "performance",
      label: "Performance",
      icon: "📈",
      score: summary.performance.average_cpu,
      suffix: "%",
      detail: `${count(summary.performance.underutilized)} underutilized · ${count(
        summary.performance.overutilized
      )} overutilized`,
      color:
        "text-purple-600 dark:text-purple-400",
      bg:
        "bg-purple-50 dark:bg-purple-500/10",
      border:
        "border-purple-100 dark:border-purple-500/20",
    },
  ];

  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-gray-900 dark:text-white">
            Environment monitoring
          </h2>

          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Security, governance and resource performance
          </p>
        </div>

        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gray-50 dark:bg-white/5">
          📊
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {monitoring.map((item) => {
          const hasScore = item.score != null;

          return (
            <div
              key={item.key}
              className={`rounded-2xl border p-5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md ${item.border} ${item.bg}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-lg shadow-sm dark:bg-white/10">
                    {item.icon}
                  </div>

                  <div>
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">
                      {item.label}
                    </p>

                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Environment health
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex items-end gap-1">
                <span
                  className={`text-3xl font-bold ${
                    hasScore
                      ? item.color
                      : "text-gray-400 dark:text-gray-500"
                  }`}
                >
                  {hasScore ? item.score : "—"}
                </span>

                {hasScore && (
                  <span className="mb-1 text-sm text-gray-500 dark:text-gray-400">
                    {item.suffix}
                  </span>
                )}
              </div>

              {hasScore && (
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/70 dark:bg-white/10">
                  <div
                    className={`h-full rounded-full ${
                      item.key === "security"
                        ? "bg-red-500"
                        : item.key === "governance"
                        ? "bg-blue-500"
                        : "bg-purple-500"
                    }`}
                    style={{
                      width: `${Math.min(
                        Number(item.score),
                        100
                      )}%`,
                    }}
                  />
                </div>
              )}

              <p className="mt-4 text-xs leading-5 text-gray-600 dark:text-gray-300">
                {item.detail}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/* Main Dashboard                                                             */
/* -------------------------------------------------------------------------- */

export default function Home() {
  const { accounts } = useMsal();

  const [summary, setSummary] =
    useState<DashboardSummary | null>(null);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshingCosts, setRefreshingCosts] =
    useState(false);

  const refresh = useCallback(
    async (signal?: AbortSignal) => {
      try {
        const value = await getDashboardSummary(signal);

        setSummary(value);
        setError("");
      } catch (reason) {
        if (!signal?.aborted) {
          setError(
            reason instanceof Error
              ? reason.message
              : "Unable to load dashboard data."
          );
        }
      } finally {
        if (!signal?.aborted) {
          setLoading(false);
        }
      }
    },
    []
  );

  useEffect(() => {
    const controller = new AbortController();

    void refresh(controller.signal);

    const poll = window.setInterval(
      () => void refresh(),
      60_000
    );

    return () => {
      controller.abort();
      window.clearInterval(poll);
    };
  }, [refresh]);

  const refreshCosts = async () => {
    setRefreshingCosts(true);

    try {
      const account = accounts[0];

      if (!account) {
        throw new Error(
          "Your Microsoft sign-in session expired. Please sign in again."
        );
      }

      await refreshDashboardCosts(
        await getAzureManagementAccessToken(account)
      );

      await refresh();
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Unable to refresh Azure cost data."
      );
    } finally {
      setRefreshingCosts(false);
    }
  };

  if (loading && !summary) {
    return (
      <div className="p-8 text-sm text-gray-500">
        Loading FinOps dashboard…
      </div>
    );
  }

  if (error && !summary) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">
        {error}
      </div>
    );
  }

  if (!summary) return null;

  const currency = summary.cost.currency ?? "USD";

  const potentialPercent =
    summary.cost.monthly &&
    summary.savings.potential_monthly
      ? `${(
          (summary.savings.potential_monthly /
            summary.cost.monthly) *
          100
        ).toFixed(1)}% of spend`
      : "No cost baseline available";

  return (
    <>
      <PageMeta
        title="FinOps Agent · Executive Dashboard"
        description="Azure FinOps executive dashboard"
      />

      <div className="space-y-6">

        {/* ---------------------------------------------------------------- */}
        {/* Header                                                           */}
        {/* ---------------------------------------------------------------- */}

        <header>
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-brand-500">
                EXECUTIVE SUMMARY
              </p>

              <h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
                Your Azure FinOps overview
              </h1>

              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Last updated{" "}
                {new Date(
                  summary.generated_at
                ).toLocaleString()}{" "}
                ·{" "}
                {summary.cost.cost_type ??
                  "Cost provenance unavailable"}
              </p>
            </div>

            <button
              type="button"
              onClick={() => void refreshCosts()}
              disabled={refreshingCosts}
              className="rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-600 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {refreshingCosts
                ? "Refreshing Azure costs…"
                : "Refresh Azure costs"}
            </button>
          </div>

          {error && (
            <p className="mt-2 text-sm text-amber-600">
              Showing last successful result. Refresh failed:{" "}
              {error}
            </p>
          )}
        </header>

        {/* ---------------------------------------------------------------- */}
        {/* KPI cards                                                        */}
        {/* ---------------------------------------------------------------- */}

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          <Card
            label="Monthly cost"
            value={amount(
              summary.cost.monthly,
              currency
            )}
            detail={
              summary.cost.is_estimated === true
                ? `Estimated · ${
                    summary.cost.cost_source ??
                    "source unavailable"
                  }`
                : summary.cost.is_estimated === false
                ? "Actual cost evidence"
                : "Cost estimation mode unavailable"
            }
          />

          <Card
            label="Potential savings"
            value={amount(
              summary.savings.potential_monthly,
              currency
            )}
            detail={`${potentialPercent} · ${summary.agent.recommendations} recommendations`}
          />

          <Card
            label="Realized savings"
            value={amount(
              summary.savings.realized_monthly,
              currency
            )}
            detail={`${summary.savings.verified_actions} verified actions`}
          />

          <Card
            label="Resources"
            value={count(summary.resources.total)}
            detail={`${count(
              summary.resources.optimization_candidates
            )} optimization candidates`}
          />

          <Card
            label="AI agent"
            value={summary.agent.status}
            detail={`${summary.agent.pending_approval} pending · ${summary.agent.executed} executed · ${summary.agent.verification_pending} awaiting verification`}
          />
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* Cost overview + composition                                     */}
        {/* ---------------------------------------------------------------- */}

        <div className="grid gap-6 xl:grid-cols-3">

          <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm xl:col-span-2 dark:border-gray-800 dark:bg-white/[0.03]">
            <Title>Cost overview</Title>

            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {[
                [
                  "Current period",
                  amount(
                    summary.cost.monthly,
                    currency
                  ),
                ],
                [
                  "Previous period",
                  amount(
                    summary.cost.previous,
                    currency
                  ),
                ],
                [
                  "Change",
                  summary.cost.change_percent == null
                    ? "No data available"
                    : `${summary.cost.change_percent.toFixed(
                        1
                      )}%`,
                ],
                [
                  "Forecast",
                  amount(
                    summary.cost.forecast,
                    currency
                  ),
                ],
              ].map(([label, value]) => (
                <div
                  key={label}
                  className="rounded-xl bg-gray-50 p-3 dark:bg-white/5"
                >
                  <p className="text-xs text-gray-500">
                    {label}
                  </p>

                  <p className="mt-1 font-semibold text-gray-900 dark:text-white">
                    {value}
                  </p>
                </div>
              ))}
            </div>

            <div className="mt-5">
              <CostTrendChart
                trend={summary.cost_overview.trend}
                currency={currency}
              />
            </div>
          </section>

          <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
            <Title>Cost composition</Title>

            <CostComposition
              items={summary.cost_composition}
              monthlyCost={summary.cost.monthly}
              currency={currency}
            />
          </section>
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* Cost drivers                                                     */}
        {/* ---------------------------------------------------------------- */}

        <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
          <Title
            to="/cost-drivers"
            label="View all cost drivers"
          >
            Top cost drivers
          </Title>

          <CostDrivers items={summary.cost_drivers} currency={currency} />
        </section>

        <div className="grid gap-6 xl:grid-cols-3">

          <div>
            <OptimizationOpportunities
              opportunities={
                summary.optimization_opportunities
              }
              potentialSavings={
                summary.savings.potential_monthly
              }
              currency={currency}
            />
          </div>

          <div className="xl:col-span-2">
            <Recommendations
              recommendations={summary.recommendations}
              currency={currency}
            />
          </div>
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* Environment Monitoring                                           */}
        {/* ---------------------------------------------------------------- */}

        <EnvironmentMonitoring summary={summary} />

        {/* ---------------------------------------------------------------- */}
        {/* Recent Actions                                                    */}
        {/* ---------------------------------------------------------------- */}

        <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
          <Title
            to="/executions"
            label="View executions"
          >
            Recent optimization actions
          </Title>

          <Table
            headers={[
              "Action",
              "Resource",
              "Execution",
              "Verification",
              "Realized savings",
              "Timestamp",
            ]}
            rows={summary.recent_actions.map(
              (item) => [
                item.action ?? "No data",
                item.resource_id,
                item.execution_status ?? "No data",
                item.verification_status ??
                  "Not executed",
                amount(
                  item.realized_savings,
                  currency
                ),
                item.timestamp
                  ? new Date(
                      item.timestamp
                    ).toLocaleString()
                  : "No data",
              ]
            )}
          />
        </section>

        {/* ---------------------------------------------------------------- */}
        {/* Alerts                                                            */}
        {/* ---------------------------------------------------------------- */}

        <section className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
          <Title to="/alerts">Alerts</Title>

          {summary.alerts.length ? (
            <div className="space-y-3">
              {summary.alerts.map(
                (item, index) => {
                  const styles = alertStyles(
                    item.severity
                  );

                  return (
                    <div
                      key={`${item.title}-${index}`}
                      className={`rounded-xl border p-4 transition-shadow hover:shadow-sm ${styles.container}`}
                    >
                      <div className="flex items-start gap-3">
                        <span
                          className="mt-0.5 text-sm"
                          aria-hidden="true"
                        >
                          {styles.icon}
                        </span>

                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span
                              className={`rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide ${styles.badge}`}
                            >
                              {item.severity}
                            </span>

                            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                              {item.title}
                            </h3>
                          </div>

                          <p className="mt-2 text-sm leading-5 text-gray-600 dark:text-gray-300">
                            {item.description}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                }
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 py-10 text-center dark:border-gray-800">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-100 dark:bg-white/10">
                🔔
              </div>

              <p className="mt-3 text-sm font-medium text-gray-900 dark:text-white">
                No alerts
              </p>

              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Your Azure environment has no active
                alerts.
              </p>
            </div>
          )}
        </section>
      </div>
    </>
  );
}

/* -------------------------------------------------------------------------- */
/* Table                                                                      */
/* -------------------------------------------------------------------------- */

function Table({
  headers,
  rows,
}: {
  headers: string[];
  rows: string[][];
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[550px] text-left text-sm">
        <thead className="border-b text-xs uppercase text-gray-500 dark:border-gray-800">
          <tr>
            {headers.map((header) => (
              <th
                key={header}
                className="pb-3 font-medium"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {rows.length ? (
            rows.map((row, index) => (
              <tr
                key={`${row[0]}-${index}`}
                className="border-b border-gray-50 last:border-0 dark:border-gray-800/60"
              >
                {row.map((value, cell) => (
                  <td
                    key={cell}
                    className="py-3 text-gray-700 dark:text-gray-300"
                  >
                    {value}
                  </td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td
                className="py-4 text-gray-500"
                colSpan={headers.length}
              >
                No data available
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Alert styles                                                               */
/* -------------------------------------------------------------------------- */

function alertStyles(severity: string) {
  const value = severity.toLowerCase();

  if (value.includes("critical")) {
    return {
      container:
        "border-red-200 bg-red-50 dark:border-red-500/20 dark:bg-red-500/10",
      badge:
        "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300",
      icon: "🔴",
    };
  }

  if (value.includes("high")) {
    return {
      container:
        "border-orange-200 bg-orange-50 dark:border-orange-500/20 dark:bg-orange-500/10",
      badge:
        "bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-300",
      icon: "🟠",
    };
  }

  if (
    value.includes("medium") ||
    value.includes("warning")
  ) {
    return {
      container:
        "border-yellow-200 bg-yellow-50 dark:border-yellow-500/20 dark:bg-yellow-500/10",
      badge:
        "bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-300",
      icon: "🟡",
    };
  }

  if (value.includes("pending")) {
    return {
      container:
        "border-yellow-200 bg-yellow-50 dark:border-yellow-500/20 dark:bg-yellow-500/10",
      badge:
        "bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-300",
      icon: "🟡",
    };
  }

  if (
    value.includes("success") ||
    value.includes("resolved") ||
    value.includes("approved")
  ) {
    return {
      container:
        "border-green-200 bg-green-50 dark:border-green-500/20 dark:bg-green-500/10",
      badge:
        "bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-300",
      icon: "🟢",
    };
  }

  if (value.includes("info")) {
    return {
      container:
        "border-blue-200 bg-blue-50 dark:border-blue-500/20 dark:bg-blue-500/10",
      badge:
        "bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300",
      icon: "🔵",
    };
  }

  return {
    container:
      "border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-white/5",
    badge:
      "bg-gray-100 text-gray-700 dark:bg-white/10 dark:text-gray-300",
    icon: "⚪",
  };
}