import { useCallback, useEffect, useMemo, useState } from "react";
import { useMsal } from "@azure/msal-react";
import {
  Activity,
  ChevronRight,
  Database,
  DollarSign,
  RefreshCw,
  Search,
  Server,
  X,
} from "lucide-react";
import PageMeta from "../components/common/PageMeta";
import {
  getDashboardSummary,
  getResourceDetails,
  getResourceInventory,
  type DashboardSummary,
  type ResourceDetails,
} from "../services/dashboard";
import { getAzureManagementAccessToken } from "../lib/entra";

type Resource = DashboardSummary["resource_inventory"][number];
type StatusFilter = "all" | "active" | "other";

type MetricEvidence = {
  value?: number | string | null;
  status?: string | null;
  source?: string | null;
  period?: string | null;
  reason?: string | null;
};

type MetricPoint = {
  timestamp: string;
  value: number;
};

function formatAmount(
  value: number | null | undefined,
  currency: string
) {
  if (value == null) return "No cost data";

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(value);
}

function normalized(value: string | null | undefined) {
  return value?.trim() || "Unavailable";
}

function isActive(resource: Resource) {
  return ["running", "succeeded", "available", "active"].includes(
    (resource.provisioning_state ?? "").toLowerCase()
  );
}

function formatMetricValue(
  value: number | string | null | undefined,
  label: string
) {
  if (value == null) return "—";

  if (typeof value === "string") return value;

  const lower = label.toLowerCase();

  if (lower.includes("cpu")) {
    return `${value.toFixed(2)}%`;
  }

  if (
    lower.includes("network") ||
    lower.includes("bytes") ||
    lower.includes("storage")
  ) {
    if (Math.abs(value) >= 1_000_000_000) {
      return `${(value / 1_000_000_000).toFixed(2)} GB`;
    }

    if (Math.abs(value) >= 1_000_000) {
      return `${(value / 1_000_000).toFixed(2)} MB`;
    }

    if (Math.abs(value) >= 1_000) {
      return `${(value / 1_000).toFixed(2)} KB`;
    }
  }

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
  }).format(value);
}

function metricLabel(label: string) {
  return label
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function isAvailableMetric(evidence: MetricEvidence) {
  if (!evidence) return false;

  if (evidence.value === null || evidence.value === undefined) {
    return false;
  }

  if (
    evidence.status &&
    evidence.status.toLowerCase() === "unavailable"
  ) {
    return false;
  }

  return true;
}

function Kpi({
  label,
  value,
  detail,
  Icon,
}: {
  label: string;
  value: string;
  detail: string;
  Icon: typeof Server;
}) {
  return (
    <article className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
            {label}
          </p>

          <p className="mt-3 text-2xl font-semibold text-gray-900 dark:text-white">
            {value}
          </p>
        </div>

        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-300">
          <Icon size={18} />
        </span>
      </div>

      <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
        {detail}
      </p>
    </article>
  );
}

function MetricChart({
  label,
  evidence,
}: {
  label: string;
  evidence: MetricEvidence;
}) {
  const currentValue =
    typeof evidence.value === "number" ? evidence.value : null;

  /*
   * The current backend returns aggregated metric values.
   * When a time-series `points` array becomes available, this component
   * automatically uses it.
   */
  const points = (
    evidence as MetricEvidence & {
      points?: MetricPoint[];
    }
  ).points;

  const hasSeries = Array.isArray(points) && points.length > 1;

  const values = hasSeries
    ? points!.map((point) => point.value)
    : currentValue != null
      ? [currentValue]
      : [];

  if (!values.length) return null;

  const max = Math.max(...values);
  const min = Math.min(...values);

  const width = 800;
  const height = 220;
  const paddingX = 20;
  const paddingY = 20;

  const range = max - min || 1;

  const chartPoints = values.map((value, index) => {
    const x =
      values.length === 1
        ? width / 2
        : paddingX +
          (index / (values.length - 1)) * (width - paddingX * 2);

    const y =
      height -
      paddingY -
      ((value - min) / range) * (height - paddingY * 2);

    return `${x},${y}`;
  });

  const path = chartPoints.join(" ");

  return (
    <article className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-gray-900 dark:text-white">
            {metricLabel(label)}
          </h3>

          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {evidence.source ?? "Azure Monitor"}
            {evidence.period ? ` · ${evidence.period}` : ""}
          </p>
        </div>

        {currentValue != null && (
          <div className="text-right">
            <p className="text-xl font-semibold text-gray-900 dark:text-white">
              {formatMetricValue(currentValue, label)}
            </p>

            <p className="text-xs text-gray-500 dark:text-gray-400">
              Current value
            </p>
          </div>
        )}
      </div>

      <div className="mt-5 h-[220px] w-full">
        {hasSeries ? (
          <svg
            viewBox={`0 0 ${width} ${height}`}
            className="h-full w-full overflow-visible"
            role="img"
            aria-label={`${metricLabel(label)} chart`}
          >
            <line
              x1={paddingX}
              y1={height - paddingY}
              x2={width - paddingX}
              y2={height - paddingY}
              stroke="currentColor"
              className="text-gray-200 dark:text-gray-800"
            />

            <line
              x1={paddingX}
              y1={paddingY}
              x2={width - paddingX}
              y2={paddingY}
              stroke="currentColor"
              className="text-gray-100 dark:text-gray-800"
            />

            <polyline
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={path}
              className="text-brand-500"
            />

            {values.map((value, index) => {
              const [x, y] = chartPoints[index].split(",");

              return (
                <circle
                  key={`${label}-${index}`}
                  cx={x}
                  cy={y}
                  r="4"
                  fill="currentColor"
                  className="text-brand-500"
                >
                  <title>
                    {formatMetricValue(value, label)}
                  </title>
                </circle>
              );
            })}
          </svg>
        ) : (
          <div className="flex h-full items-center justify-center rounded-lg bg-gray-50 text-sm text-gray-500 dark:bg-white/[0.04] dark:text-gray-400">
            No time-series data available
          </div>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
        <span>
          {hasSeries
            ? `${values.length} data points`
            : "Latest available value"}
        </span>

        {hasSeries && (
          <span>
            Min {formatMetricValue(min, label)} · Max{" "}
            {formatMetricValue(max, label)}
          </span>
        )}
      </div>
    </article>
  );
}

export default function ActiveResources() {
  const { accounts } = useMsal();

  const [summary, setSummary] =
    useState<DashboardSummary | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [query, setQuery] = useState("");
  const [type, setType] = useState("all");
  const [group, setGroup] = useState("all");
  const [region, setRegion] = useState("all");
  const [status, setStatus] =
    useState<StatusFilter>("all");

  const [selectedId, setSelectedId] =
    useState<string | null>(null);

  const [details, setDetails] =
    useState<ResourceDetails | null>(null);

  const [detailsLoading, setDetailsLoading] =
    useState(false);

  const [detailsError, setDetailsError] =
    useState("");

  const [detailsTab, setDetailsTab] =
    useState<"Overview" | "Usage & Metrics">("Overview");

  const [page, setPage] = useState(1);

  const pageSize = 25;

  const [inventoryPage, setInventoryPage] =
    useState<{
      items: Resource[];
      total: number;
      has_next: boolean;
      has_previous: boolean;
    }>({
      items: [],
      total: 0,
      has_next: false,
      has_previous: false,
    });

  const load = useCallback(async () => {
    setLoading(true);

    try {
      const [nextSummary, nextPage] =
        await Promise.all([
          getDashboardSummary(),
          getResourceInventory({
            page,
            pageSize,
            search: query,
            resourceType: type,
            resourceGroup: group,
            region,
            status,
          }),
        ]);

      setSummary(nextSummary);
      setInventoryPage(nextPage);
      setError("");
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Unable to load resource inventory."
      );
    } finally {
      setLoading(false);
    }
  }, [
    group,
    page,
    pageSize,
    query,
    region,
    status,
    type,
  ]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    setPage(1);
  }, [query, type, group, region, status]);

  useEffect(() => {
    if (!selectedId) {
      setDetails(null);
      setDetailsError("");
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

  const costs = useMemo(
    () =>
      new Map(
        (summary?.cost_resources ?? []).map(
          (item) => [
            item.resource_id.toLowerCase(),
            item,
          ]
        )
      ),
    [summary]
  );

  const types = useMemo(
    () =>
      [
        ...new Set(
          inventory.map((item) =>
            normalized(item.resource_type)
          )
        ),
      ].sort(),
    [inventory]
  );

  const groups = useMemo(
    () =>
      [
        ...new Set(
          inventory.map((item) =>
            normalized(item.resource_group)
          )
        ),
      ].sort(),
    [inventory]
  );

  const regions = useMemo(
    () =>
      [
        ...new Set(
          inventory.map((item) =>
            normalized(item.location)
          )
        ),
      ].sort(),
    [inventory]
  );

  const selected =
    inventory.find(
      (item) => item.resource_id === selectedId
    ) ?? null;

  const currency = summary?.cost.currency ?? "USD";

  const totalCost = [
    ...costs.values(),
  ].reduce(
    (sum, item) =>
      sum + (item.monthly_cost ?? 0),
    0
  );

  const activeCount = inventoryPage.total;

  const availableMetrics = useMemo(() => {
    if (!details?.metrics?.values) return [];

    return Object.entries(details.metrics.values).filter(
      ([, evidence]) =>
        isAvailableMetric(
          evidence as MetricEvidence
        )
    );
  }, [details]);

  return (
    <>
      <PageMeta
        title="FinOps Agent · Active Resources"
        description="Azure resource inventory and observability"
      />

      <div className="space-y-6">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-brand-500">
              RESOURCE INVENTORY
            </p>

            <h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
              Active Resources
            </h1>

            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Resources discovered in the connected subscription.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void load()}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-60"
          >
            <RefreshCw
              size={16}
              className={
                loading ? "animate-spin" : ""
              }
            />
            Refresh
          </button>
        </header>

        {error && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-300">
            Showing the last successful result.
            Refresh failed: {error}
          </div>
        )}

        {selectedId && (
          <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <p className="text-xs font-semibold uppercase tracking-wider text-brand-500">
                  Resource observability
                </p>

                <h2 className="mt-1 text-xl font-semibold text-gray-900 dark:text-white">
                  {normalized(
                    selected?.resource_name
                  )}
                </h2>

                <p className="mt-1 break-all text-xs text-gray-500 dark:text-gray-400">
                  {selectedId}
                </p>
              </div>

              <button
                type="button"
                onClick={() => setSelectedId(null)}
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-900 dark:hover:bg-white/10 dark:hover:text-white"
                aria-label="Close resource details"
              >
                <X size={18} />
              </button>
            </div>

            {detailsLoading && (
              <div className="mt-6 flex items-center gap-2 text-sm text-gray-500">
                <RefreshCw
                  size={16}
                  className="animate-spin"
                />
                Loading resource observability...
              </div>
            )}

            {detailsError && (
              <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">
                {detailsError}
              </div>
            )}

            {details && (
              <>
                <nav className="mt-6 flex gap-2 overflow-x-auto border-b border-gray-200 dark:border-gray-800">
                  {(
                    [
                      "Overview",
                      "Usage & Metrics",
                    ] as const
                  ).map((tab) => (
                    <button
                      key={tab}
                      type="button"
                      onClick={() =>
                        setDetailsTab(tab)
                      }
                      className={`whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium ${
                        detailsTab === tab
                          ? "border-brand-500 text-brand-600 dark:text-brand-400"
                          : "border-transparent text-gray-500 hover:text-gray-900 dark:hover:text-white"
                      }`}
                    >
                      {tab}
                    </button>
                  ))}
                </nav>

                {detailsTab === "Overview" && (
                  <div className="mt-6 space-y-6">
                    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                      <Kpi
                        label="Monthly cost"
                        value={formatAmount(
                          details.cost.monthly,
                          details.cost.currency ??
                            currency
                        )}
                        detail={
                          details.cost.source ??
                          "Cost data unavailable"
                        }
                        Icon={DollarSign}
                      />

                      <Kpi
                        label="Metrics available"
                        value={String(
                          availableMetrics.length
                        )}
                        detail="Azure Monitor metrics currently available"
                        Icon={Activity}
                      />

                      <Kpi
                        label="Resource type"
                        value={normalized(
                          details.resource.identity
                            ?.type
                        )}
                        detail="Azure resource type"
                        Icon={Database}
                      />

                      <Kpi
                        label="Status"
                        value={normalized(
                          details.resource.runtime
                            ?.provisioning_state
                        )}
                        detail="Current provisioning state"
                        Icon={Server}
                      />
                    </div>

                    <div>
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                        Resource information
                      </h3>

                      <div className="mt-3 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                        {Object.entries({
                          id: details.resource.identity
                            ?.id,
                          name: details.resource.identity
                            ?.name,
                          type: details.resource.identity
                            ?.type,
                          resource_group:
                            details.resource.identity
                              ?.resource_group,
                          region:
                            details.resource.identity
                              ?.location,
                          provisioning_state:
                            details.resource.runtime
                              ?.provisioning_state,
                          power_state:
                            details.resource.runtime
                              ?.power_state,
                          sku: details.resource
                            .configuration?.sku,
                          os_type:
                            details.resource
                              .configuration?.os_type,
                        }).map(
                          ([label, value]) => (
                            <div
                              key={label}
                              className="rounded-lg bg-gray-50 p-4 dark:bg-white/[0.04]"
                            >
                              <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                                {label.replace(
                                  /_/g,
                                  " "
                                )}
                              </p>

                              <p className="mt-2 break-words text-sm font-semibold text-gray-900 dark:text-white">
                                {value == null ||
                                value === ""
                                  ? "Unavailable"
                                  : String(value)}
                              </p>
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {detailsTab === "Usage & Metrics" && (
                  <div className="mt-6 space-y-6">
                    <div className="rounded-xl border border-gray-200 bg-gray-50 p-5 dark:border-gray-800 dark:bg-white/[0.03]">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <h3 className="font-semibold text-gray-900 dark:text-white">
                            Available metrics
                          </h3>

                          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                            Only metrics with real data are displayed.
                          </p>
                        </div>

                        <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-600 dark:bg-brand-500/10 dark:text-brand-300">
                          {availableMetrics.length} available
                        </span>
                      </div>
                    </div>

                    {availableMetrics.length === 0 ? (
                      <div className="rounded-xl border border-gray-200 bg-white p-10 text-center dark:border-gray-800 dark:bg-white/[0.03]">
                        <Activity
                          size={32}
                          className="mx-auto text-gray-400"
                        />

                        <h3 className="mt-3 font-semibold text-gray-900 dark:text-white">
                          No metrics available
                        </h3>

                        <p className="mx-auto mt-1 max-w-md text-sm text-gray-500 dark:text-gray-400">
                          Azure Monitor did not return usable
                          metric data for this resource.
                        </p>
                      </div>
                    ) : (
                      <>
                        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                          {availableMetrics.map(
                            ([label, rawEvidence]) => {
                              const evidence =
                                rawEvidence as MetricEvidence;

                              return (
                                <article
                                  key={label}
                                  className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]"
                                >
                                  <div className="flex items-start justify-between gap-3">
                                    <div className="min-w-0">
                                      <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                                        {metricLabel(
                                          label
                                        )}
                                      </p>

                                      <p className="mt-3 text-2xl font-semibold text-gray-900 dark:text-white">
                                        {formatMetricValue(
                                          evidence.value,
                                          label
                                        )}
                                      </p>
                                    </div>

                                    <Activity
                                      size={18}
                                      className="shrink-0 text-brand-500"
                                    />
                                  </div>

                                  <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                                    {evidence.source ??
                                      "Azure Monitor"}
                                  </p>
                                </article>
                              );
                            }
                          )}
                        </div>

                        <div className="space-y-5">
                          {availableMetrics.map(
                            ([label, rawEvidence]) => (
                              <MetricChart
                                key={`chart-${label}`}
                                label={label}
                                evidence={
                                  rawEvidence as MetricEvidence
                                }
                              />
                            )
                          )}
                        </div>
                      </>
                    )}
                  </div>
                )}
              </>
            )}
          </section>
        )}

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Kpi
            label="Total resources"
            value={String(inventory.length)}
            detail="Discovered resource inventory"
            Icon={Server}
          />

          <Kpi
            label="Running / active"
            value={String(activeCount)}
            detail="Based on provisioning state"
            Icon={Activity}
          />

          <Kpi
            label="Monthly estimated cost"
            value={formatAmount(
              totalCost,
              currency
            )}
            detail={
              summary?.cost.is_estimated
                ? "Estimated cost evidence"
                : "Persisted cost evidence"
            }
            Icon={DollarSign}
          />

          <Kpi
            label="Resource types"
            value={String(types.length)}
            detail="Unique resource types discovered"
            Icon={Database}
          />
        </div>

        <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
          <div className="mb-5">
            <h2 className="font-semibold text-gray-900 dark:text-white">
              Resource inventory
            </h2>

            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {inventoryPage.total} resources match the
              current filters. Page {page}.
            </p>
          </div>

          <div className="mb-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            <label className="relative">
              <Search
                className="pointer-events-none absolute left-3 top-3 text-gray-400"
                size={16}
              />

              <input
                type="search"
                value={query}
                onChange={(event) =>
                  setQuery(event.target.value)
                }
                placeholder="Search resources"
                className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-9 pr-3 text-sm text-gray-900 outline-none focus:border-brand-500 dark:border-gray-700 dark:bg-gray-900 dark:text-white"
              />
            </label>

            <label>
              <span className="sr-only">
                Resource type
              </span>

              <select
                value={type}
                onChange={(event) =>
                  setType(event.target.value)
                }
                className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
              >
                <option value="all">
                  All types
                </option>

                {types.map((value) => (
                  <option key={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span className="sr-only">
                Resource group
              </span>

              <select
                value={group}
                onChange={(event) =>
                  setGroup(event.target.value)
                }
                className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
              >
                <option value="all">
                  All resource groups
                </option>

                {groups.map((value) => (
                  <option key={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span className="sr-only">
                Region
              </span>

              <select
                value={region}
                onChange={(event) =>
                  setRegion(event.target.value)
                }
                className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
              >
                <option value="all">
                  All regions
                </option>

                {regions.map((value) => (
                  <option key={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span className="sr-only">
                Status
              </span>

              <select
                value={status}
                onChange={(event) =>
                  setStatus(
                    event.target.value as StatusFilter
                  )
                }
                className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
              >
                <option value="all">
                  All statuses
                </option>

                <option value="active">
                  Running / active
                </option>

                <option value="other">
                  Other states
                </option>
              </select>
            </label>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[1000px] text-left text-sm">
              <thead className="border-b border-gray-200 text-xs uppercase tracking-wider text-gray-500 dark:border-gray-800">
                <tr>
                  <th className="pb-3 pr-4">
                    Resource
                  </th>

                  <th className="pb-3 pr-4">
                    Type
                  </th>

                  <th className="pb-3 pr-4">
                    Status
                  </th>

                  <th className="pb-3 pr-4">
                    Resource group
                  </th>

                  <th className="pb-3 pr-4">
                    Region
                  </th>

                  <th className="pb-3 pr-4">
                    SKU
                  </th>

                  <th className="pb-3 pr-4 text-right">
                    Monthly cost
                  </th>

                  <th className="pb-3" />
                </tr>
              </thead>

              <tbody>
                {inventory.length ? (
                  inventory.map((item) => {
                    const cost = costs.get(
                      item.resource_id.toLowerCase()
                    );

                    return (
                      <tr
                        key={item.resource_id}
                        onClick={() =>
                          setSelectedId(
                            item.resource_id
                          )
                        }
                        className="cursor-pointer border-b border-gray-50 transition hover:bg-gray-50 dark:border-gray-800/60 dark:hover:bg-white/[0.03]"
                      >
                        <td className="max-w-[230px] py-4 pr-4">
                          <p className="truncate font-semibold text-gray-900 dark:text-white">
                            {normalized(
                              item.resource_name
                            )}
                          </p>

                          <p className="mt-0.5 truncate text-xs text-gray-500">
                            {item.resource_id}
                          </p>
                        </td>

                        <td className="max-w-[160px] truncate py-4 pr-4 text-gray-600 dark:text-gray-300">
                          {normalized(
                            item.resource_type
                          )}
                        </td>

                        <td className="py-4 pr-4">
                          <span
                            className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                              isActive(item)
                                ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
                                : "bg-gray-100 text-gray-600 dark:bg-white/10 dark:text-gray-300"
                            }`}
                          >
                            {normalized(
                              item.provisioning_state
                            )}
                          </span>
                        </td>

                        <td className="py-4 pr-4 text-gray-600 dark:text-gray-300">
                          {normalized(
                            item.resource_group
                          )}
                        </td>

                        <td className="py-4 pr-4 text-gray-600 dark:text-gray-300">
                          {normalized(
                            item.location
                          )}
                        </td>

                        <td className="py-4 pr-4 text-gray-600 dark:text-gray-300">
                          {normalized(item.sku)}
                        </td>

                        <td className="py-4 pr-4 text-right font-semibold text-gray-900 dark:text-white">
                          {formatAmount(
                            cost?.monthly_cost,
                            currency
                          )}
                        </td>

                        <td className="py-4">
                          <ChevronRight
                            size={18}
                            className="text-gray-400"
                          />
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td
                      colSpan={8}
                      className="py-12 text-center text-sm text-gray-500"
                    >
                      No resources match the selected
                      filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="mt-5 flex items-center justify-between gap-3 border-t border-gray-100 pt-4 text-sm dark:border-gray-800">
            <span className="text-gray-500">
              Showing{" "}
              {inventoryPage.total === 0
                ? 0
                : (page - 1) * pageSize + 1}
              –
              {Math.min(
                page * pageSize,
                inventoryPage.total
              )}{" "}
              of {inventoryPage.total}
            </span>

            <div className="flex gap-2">
              <button
                type="button"
                disabled={
                  !inventoryPage.has_previous ||
                  loading
                }
                onClick={() =>
                  setPage(
                    (value) => value - 1
                  )
                }
                className="rounded-lg border border-gray-200 px-3 py-2 disabled:opacity-40 dark:border-gray-700"
              >
                Previous
              </button>

              <button
                type="button"
                disabled={
                  !inventoryPage.has_next ||
                  loading
                }
                onClick={() =>
                  setPage(
                    (value) => value + 1
                  )
                }
                className="rounded-lg border border-gray-200 px-3 py-2 disabled:opacity-40 dark:border-gray-700"
              >
                Next
              </button>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}