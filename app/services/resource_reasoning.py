'''Resource-specific, evidence-driven Azure FinOps decisions.'''
from __future__ import annotations
from typing import Any
VM = "microsoft.compute/virtualmachines"
ACR = "microsoft.containerregistry/registries"
DISK = "microsoft.compute/disks"
PUBLIC_IP = "microsoft.network/publicipaddresses"
APP_SERVICE = "microsoft.web/sites"
SQL_DB = "microsoft.sql/servers/databases"


def _number(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None

def _metric(evidence: dict, *names: str) -> float | None:
    metrics = evidence.get("metrics") or {}
    details = evidence.get("metric_details") or {}
    for name in names:
        value = metrics.get(name)
        if value is None:
            value = (details.get(name) or {}).get("value")
        value = _number(value)
        if value is not None:
            return value
    return None

def _configuration(evidence: dict) -> dict:
    return evidence.get("configuration") or {}


def _metric_text(evidence: dict) -> str:
    metrics = evidence.get("metrics") or {}
    if not metrics:
        return "Unavailable"
    return "; ".join(f"{name}={value}" for name, value in metrics.items())


def _missing(evidence: dict, reason: str | None = None) -> dict:
    config = _configuration(evidence)
    missing = []
    if not evidence.get("metric_available"):
        missing.append(reason or evidence.get("metric_unavailable_reason") or "resource-specific utilization metrics")
    if not evidence.get("configuration_available"):
        missing.append("resource configuration")
    if evidence.get("cost") is None:
        missing.append("monthly pricing information")
    return _result(
        "insufficient_evidence",
        "Insufficient evidence for a resource-specific optimization.",
        "No safe optimization can be confirmed because " + ", ".join(missing or ["the required evidence is incomplete"]) + ".",
               {
            DISK: "Collect disk IOPS/throughput and attachment-state evidence before changing this resource.",
            SQL_DB: "Collect SQL CPU/DTU/vCore, storage, and workload evidence before changing this resource.",
            VM: "Collect VM CPU, network, and disk utilization metrics before changing this resource.",
        }.get(str(evidence.get("resource_type") or "").casefold(), "Collect the missing resource-specific metrics, configuration, dependency information, and pricing before changing this resource."),
        "Not quantifiable from available evidence because the data required to justify and price an optimization is incomplete.",
        "Low",
        evidence,
        config,
    )


def _result(action: str, finding: str, why: str, next_action: str, savings: str, confidence: str, evidence: dict, configuration: dict) -> dict:
    return {"action": action, "finding": finding, "why": why, "next_action": next_action, "savings": savings, "confidence": confidence, "metrics": _metric_text(evidence), "configuration": configuration}


def _validated_vm_savings(evidence: dict, persisted: dict | None) -> float | None:
    if not persisted or str(persisted.get("resource_id", "")).casefold() != str(evidence.get("resource_id", "")).casefold():
        return None
    action = str(persisted.get("action") or persisted.get("recommended_action") or "").casefold()
    savings = _number(persisted.get("potential_savings", persisted.get("estimated_monthly_savings")))
    cost = _number(evidence.get("cost"))
    cpu = _metric(evidence, "Percentage CPU", "CpuPercentage", "cpu_percent")
    if "resize" not in action or savings is None or savings <= 0 or cost is None or savings > cost or cpu is None or cpu >= 15:
        return None
    return savings


def _analyze_resource(evidence: dict, persisted: dict | None = None) -> dict:
    '''Return exactly one conservative primary decision for canonical evidence.'''
    resource_type = str(evidence.get("resource_type") or "").casefold()
    config = _configuration(evidence)
    metric_available = bool(evidence.get("metric_available") or evidence.get("metrics"))
    if not metric_available:
        resource_reason = {
            DISK: "disk IOPS/throughput and attachment-state evidence",
            SQL_DB: "SQL CPU/DTU/vCore, storage, and workload evidence",
            VM: "VM CPU, network, and disk utilization metrics",
        }.get(resource_type)
        return _missing(evidence, resource_reason)
    cost = _number(evidence.get("cost"))

    if resource_type == ACR:
        storage = _metric(evidence, "StorageUsed")
        pulls = _metric(evidence, "TotalPullCount")
        pushes = _metric(evidence, "TotalPushCount")
        if storage is None or pulls is None or pushes is None:
            return _missing(evidence, "StorageUsed, TotalPullCount, and TotalPushCount")
        tier = str(config.get("sku_tier") or config.get("sku") or "").casefold()
        activity = pulls + pushes
        if activity <= 0.01:
            activity_label = "extremely low"
        elif activity <= 1:
            activity_label = "very low"
        elif activity <= 100:
            activity_label = "low"
        else:
            activity_label = "material"
        storage_mb = storage / (1024 * 1024)
        finding = f"StorageUsed={storage:g} bytes (approximately {storage_mb:.0f} MB); TotalPullCount={pulls:g} and TotalPushCount={pushes:g} indicate {activity_label} observed activity."
        high_storage = storage >= 100 * 1024 * 1024
        if activity > 100:
            return _result("no_safe_optimization_identified", finding, "Pull/push activity is material, so deletion or aggressive image cleanup is not supported by this evidence.", "Review image lifecycle requirements with the owning deployment teams.", "Not quantifiable from available evidence because no safe removable storage amount or price is available.", "High" if cost is not None else "Medium", evidence, config)
        if high_storage:
            return _result("apply_image_retention_policy", finding, "High stored volume with extremely low activity supports reviewing obsolete images and applying retention. The registry is already Basic when applicable, so downgrade is not available; deletion still requires dependency evidence.", "Review image age and references, then enable a retention policy and delete only confirmed-unused images.", "Not quantifiable from available evidence because removable image size and storage pricing are unavailable.", "High", evidence, config)
        if tier == "basic":
            return _result("investigate_inactive_registry", finding, "The registry is already Basic, so SKU downgrade is unavailable. Low activity and low storage warrant dependency review, but do not justify deletion without dependency evidence.", "Confirm whether any deployment, recovery, or build workflow still requires this registry.", "Not quantifiable from available evidence because safe deletion and removable storage cost are unconfirmed.", "Medium", evidence, config)
        if tier == "premium":
            return _result("evaluate_sku_downgrade", finding, "Low activity makes a lower tier worth evaluating, but Premium-only feature usage and comparable pricing were not collected.", "Check Premium-only feature use and compare compatible Standard pricing before changing the SKU.", "Not quantifiable from available evidence because comparable lower-tier pricing is unavailable.", "Medium", evidence, config)
        return _result("investigate_inactive_registry", finding, "Low activity and low stored volume warrant dependency review; the available evidence does not justify deletion or a tier change.", "Confirm whether any deployment, recovery, or build workflow still requires this registry.", "Not quantifiable from available evidence.", "Medium", evidence, config)

    if resource_type == VM:
        cpu = _metric(evidence, "Percentage CPU", "CpuPercentage", "cpu_percent")
        if cpu is None:
            return _missing(evidence, "VM CPU utilization")
        network = [_metric(evidence, "Network In Total", "Network In"), _metric(evidence, "Network Out Total", "Network Out")]
        disk = [_metric(evidence, "Disk Read Operations/Sec"), _metric(evidence, "Disk Write Operations/Sec")]
        if cpu >= 85:
            return _result("no_safe_optimization_identified", f"Average CPU is {cpu:g}%, which is high.", "High CPU does not support downsizing.", "Review workload capacity and scaling requirements.", "Not quantifiable from available evidence because no safe cost-reduction action is supported.", "High" if cost is not None else "Medium", evidence, config)
        savings = _validated_vm_savings(evidence, persisted)
        if cpu < 15 and savings is not None:
            return _result("resize_vm", f"Average CPU is {cpu:g}%, below the low-utilization threshold; the persisted saving is {savings:.2f} against current cost {cost:.2f}.", "The current CPU evidence supports the persisted VM right-sizing recommendation and its saving does not exceed current cost.", "Validate application performance and approve a compatible smaller VM SKU.", f"ESTIMATED ${savings:.2f}/month from the validated persisted right-sizing estimate.", "High", evidence, config)
        if cpu < 15:
            return _result("resize_vm", f"Average CPU is {cpu:g}%, indicating very low utilization.", "Low CPU supports evaluating right-sizing, but a validated priced candidate is not available.", "Compare compatible smaller VM SKUs and collect their prices before resizing.", "Not quantifiable from available evidence because no validated target SKU price is available.", "Medium", evidence, config)
        return _result("no_safe_optimization_identified", f"Average CPU is {cpu:g}%, which is not low enough to support a safe downsizing recommendation.", "Current utilization evidence does not establish a cost-reduction action.", "Continue monitoring CPU and workload demand.", "Not quantifiable from available evidence.", "Medium", evidence, config)

    if resource_type == DISK:
        state = str(config.get("disk_state") or config.get("attachment_state") or "").casefold()
        managed = config.get("managed_by")
        if state in {"unattached", "unattachedstate"} or (state == "" and not managed):
            return _result("delete_unattached_disk", f"The disk configuration reports state={state or 'unattached'} and managed_by={managed or 'Unavailable'}.", "Unattached state is direct configuration evidence for a storage resource that may be removable.", "Confirm no backup or recovery workflow requires the disk, then delete it through an approved change.", f"ESTIMATED ${cost:.2f}/month if the full resource cost is avoided." if cost and cost > 0 else "Not quantifiable from available evidence because monthly cost is unavailable.", "High" if cost else "Medium", evidence, config)
        return _result("no_safe_optimization_identified", f"Disk configuration reports state={state or 'Unavailable'} and managed_by={managed or 'Unavailable'}.", "The available configuration does not establish that this disk is safely removable.", "Review disk size/SKU and workload attachment before considering a change.", "Not quantifiable from available evidence.", "Medium", evidence, config)

    if resource_type == PUBLIC_IP:
        associated = config.get("associated_resource") or config.get("ip_configuration") or config.get("managed_by")
        if not associated:
            return _result("remove_unused_public_ip", "No associated resource is present in the collected configuration.", "An unassociated public IP is a candidate for removal, but dependency confirmation is still required.", "Confirm the IP is not reserved for a future or failover service, then remove it.", f"ESTIMATED ${cost:.2f}/month if the full resource cost is avoided." if cost and cost > 0 else "Not quantifiable from available evidence.", "Medium", evidence, config)
        return _result("no_safe_optimization_identified", f"The public IP is associated with {associated}.", "Association evidence does not support removal.", "Review allocation method and SKU with the associated service owner.", "Not quantifiable from available evidence.", "High" if cost is not None else "Medium", evidence, config)

    if resource_type in {APP_SERVICE, SQL_DB}:
        metric_values = [_number(value) for value in (evidence.get("metrics") or {}).values()]
        usable = [value for value in metric_values if value is not None]
        if not usable:
            return _missing(evidence, "resource-specific utilization metrics")
        low = max(usable) < 15
        resource_label = "App Service" if resource_type == APP_SERVICE else "SQL Database"
        if low:
            action = "evaluate_sku_downgrade"
            return _result(action, f"Collected {resource_label} metrics are low; maximum observed catalog value is {max(usable):g}.", "Low utilization supports evaluating a lower compatible tier, but configuration and comparable pricing must be validated.", "Compare a compatible lower SKU/tier and verify application or database performance requirements.", "Not quantifiable from available evidence because a priced compatible target is unavailable.", "Medium", evidence, config)
        return _result("no_safe_optimization_identified", f"Collected {resource_label} metrics do not establish low utilization; maximum observed catalog value is {max(usable):g}.", "The available metrics do not support a safe scale-down recommendation.", "Continue monitoring utilization and review the current SKU against workload requirements.", "Not quantifiable from available evidence.", "Medium", evidence, config)

    return _missing(evidence, "a resource-specific metric catalog for this resource type")


def _evidence_summary(evidence: dict, decision: dict) -> list[str]:
    '''Expose only facts that materially influenced the decision.'''
    items = []
    cost = evidence.get("cost")
    if cost is not None:
        source = evidence.get("cost_source") or "unknown source"
        cost_type = evidence.get("cost_type") or ("estimated" if evidence.get("is_estimated") else "available")
        items.append(f"Cost: ${float(cost):,.2f}/month / {cost_type} / {source}")
    config = evidence.get("configuration") or {}
    for key, label in (("sku", "SKU"), ("sku_tier", "SKU tier"), ("disk_size_gb", "Disk size"), ("disk_state", "Disk state"), ("managed_by", "Attached to"), ("associated_resource", "Association")):
        if config.get(key) is not None:
            value = config[key]
            if key == "managed_by" and value:
                value = str(value).rsplit("/", 1)[-1]
            items.append(f"{label}: {value}")
    metrics = evidence.get("metrics") or {}
    for name, value in metrics.items():
        if value is not None:
            label = {"StorageUsed": "Storage", "TotalPullCount": "Pull activity", "TotalPushCount": "Push activity", "Percentage CPU": "CPU"}.get(name, name)
            if name == "StorageUsed":
                items.append(f"{label}: approximately {float(value) / (1024 * 1024):.0f} MB")
                continue
            suffix = "%" if name.casefold() in {"percentage cpu", "cpu_percent"} else ""
            items.append(f"{label}: {value}{suffix}")
    for key, label in (("retention_policy", "Retention policy"), ("soft_delete_policy", "Soft-delete policy")):
        if config.get(key) is not None:
            items.append(f"{label}: {config[key]}")
    if not items:
        items.append(f"Missing: {decision.get('why', 'resource-specific evidence')}")
    return items

def analyze_resource(evidence: dict, persisted: dict | None = None) -> dict:
    '''Build the single canonical decision consumed by API, UI, and approval projections.'''
    raw = _analyze_resource(evidence, persisted)
    confidence = str(raw.get("confidence") or "Low").title()
    score = {"High": 0.9, "Medium": 0.65, "Low": 0.25}.get(confidence, 0.25)
    action = raw.get("action")
    resource_id = evidence.get("resource_id")
    resource_name = evidence.get("resource_name") or (str(resource_id).rsplit("/", 1)[-1] if resource_id else None)
    resource_group = evidence.get("resource_group")
    if not resource_group and resource_id:
        parts = str(resource_id).split("/")
        try:
            resource_group = parts[parts.index("resourceGroups") + 1]
        except (ValueError, IndexError):
            resource_group = None
    executable = action in {"resize_vm", "delete_unattached_disk", "remove_unused_public_ip"}
    savings_text = raw.get("savings") or "Not quantifiable from available evidence."
    numeric_savings = _validated_vm_savings(evidence, persisted) if action == "resize_vm" else None
    return {
        **raw,
        "resource_id": resource_id, "resource_name": resource_name, "resource_group": resource_group,
        "resource_type": evidence.get("resource_type"), "action": action,
        "reason": raw.get("why"), "evidence": _evidence_summary(evidence, raw),
        "current_cost": evidence.get("cost"), "cost_source": evidence.get("cost_source"),
        "cost_type": evidence.get("cost_type") or ("estimated" if evidence.get("is_estimated") else None),
        "potential_savings": numeric_savings, "savings_status": "quantified" if numeric_savings is not None else "unquantifiable",
        "savings": savings_text, "confidence_score": round(score * 100), "confidence_level": confidence,
        "next_action": raw.get("next_action"), "execution_eligibility": executable,
        "requires_approval": executable,
    }
