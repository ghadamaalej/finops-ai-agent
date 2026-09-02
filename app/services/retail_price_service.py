import random
import time
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

import requests


class AzureRetailPriceService:

    BASE_URL = (
        "https://prices.azure.com/api/retail/prices"
    )
    MAX_RETRIES = 3
    RETRY_BASE_SECONDS = 1.0

    def __init__(self):

        self.session = requests.Session()
        self._price_cache = {}
        self._items_cache = {}

    # =========================================================
    # PUBLIC RETAIL PRICE API
    # =========================================================

    def get_retail_price(
        self,
        service_name: str,
        region: str | None = None,
        arm_sku_name: str | None = None,
        sku_name: str | None = None,
        meter_name: str | None = None,
        product_name: str | None = None,
        exclude_spot: bool = False,
        prefer_non_zero: bool = True,
    ):

        cache_key = (
            service_name.strip().lower(),
            (region or "").strip().lower(),
            (sku_name or "").strip().lower(),
            (meter_name or "").strip().lower(),
            "Consumption",
        )
        if cache_key in self._price_cache:
            return self._price_cache[cache_key]

        filters = [
            f"serviceName eq '{self._escape(service_name)}'",
            "priceType eq 'Consumption'",
        ]

        if region:

            filters.append(
                f"armRegionName eq "
                f"'{self._escape(region.lower().strip())}'"
            )

        if arm_sku_name:

            filters.append(
                f"armSkuName eq "
                f"'{self._escape(arm_sku_name.strip())}'"
            )

        if sku_name:

            filters.append(
                f"skuName eq "
                f"'{self._escape(sku_name.strip())}'"
            )

        if meter_name:

            filters.append(
                f"meterName eq "
                f"'{self._escape(meter_name.strip())}'"
            )

        if product_name:

            filters.append(
                f"productName eq "
                f"'{self._escape(product_name.strip())}'"
            )

        filter_expression = " and ".join(
            filters
        )

        print("\n[Retail Price API]")

        print(
            f"Service : {service_name}"
        )

        print(
            f"Region  : {region}"
        )

        print(
            f"ARM SKU : {arm_sku_name}"
        )

        print(
            f"SKU     : {sku_name}"
        )

        print(
            f"Meter   : {meter_name}"
        )

        print(
            f"Product : {product_name}"
        )

        print(
            f"Filter  : {filter_expression}"
        )

        items = self._get_cached_items(cache_key, filter_expression)

        if not items:

            print(
                "⚠️ Retail API returned no items"
            )

            self._price_cache[cache_key] = None
            return None

        consumption = [
            item
            for item in items
            if item.get("type") == "Consumption"
        ]

        if consumption:

            items = consumption

        if exclude_spot:

            non_spot = [
                item
                for item in items
                if not self._is_spot_item(item)
            ]

            if non_spot:

                items = non_spot

            else:

                print(
                    "⚠️ Only Spot pricing found."
                )

                self._price_cache[cache_key] = None
                return None

        if prefer_non_zero:

            priced = [
                item
                for item in items
                if self._safe_float(
                    item.get("retailPrice")
                ) > 0
            ]

            if priced:

                items = priced

        if sku_name:

            requested = (
                sku_name
                .upper()
                .strip()
            )

            exact = [
                item
                for item in items
                if str(
                    item.get("skuName") or ""
                ).upper().strip()
                == requested
            ]

            if exact:

                items = exact

            else:

                print(
                    f"⚠️ No exact skuName match: "
                    f"{sku_name}"
                )

                self._price_cache[cache_key] = None
                return None

        if meter_name:

            requested = (
                meter_name
                .upper()
                .strip()
            )

            exact = [
                item
                for item in items
                if str(
                    item.get("meterName") or ""
                ).upper().strip()
                == requested
            ]

            if exact:

                items = exact

            else:

                print(
                    f"⚠️ No exact meterName match: "
                    f"{meter_name}"
                )

                self._price_cache[cache_key] = None
                return None

        item = self._select_best_item(
            items=items,
            exclude_spot=exclude_spot,
        )

        if item is None:

            return None

        print(
            f"Selected meter : "
            f"{item.get('meterName')}"
        )

        print(
            f"Selected SKU   : "
            f"{item.get('skuName')}"
        )

        print(
            f"Selected price : "
            f"{item.get('retailPrice')}"
        )

        result = self._normalize_item(item)
        self._price_cache[cache_key] = result
        return result

    # =========================================================
    # VM SKU DISCOVERY
    # =========================================================

    def get_compatible_vm_skus(
        self,
        region: str,
        current_sku: str,
        os_type: str | None = None,
    ) -> list[str]:
        '''Return only smaller SKUs present in the Retail Prices catalog.'''
        # Compatibility is limited to the current SKU family and actual
        # catalog records; this method never manufactures a SKU name.
        import re
        match = re.fullmatch(r"(Standard_[A-Za-z]+?)(\d+)(.*)", str(current_sku or "").strip())
        if not match:
            return []
        family, current_size, suffix = match.group(1), int(match.group(2)), match.group(3)
        region = str(region or "").strip().lower()
        if not region or current_size <= 1:
            return []
        filter_expression = " and ".join([
            "serviceName eq 'Virtual Machines'",
            "priceType eq 'Consumption'",
            f"armRegionName eq '{self._escape(region)}'",
        ])
        cache_key = ("virtual machines", region, "__sku_catalog__", "", "Consumption")
        items = self._get_cached_items(cache_key, filter_expression)
        discovered = set()
        for item in items:
            arm_sku = str(item.get("armSkuName") or "").strip()
            candidate_match = re.fullmatch(r"(Standard_[A-Za-z]+?)(\d+)(.*)", arm_sku)
            if not candidate_match:
                continue
            if candidate_match.group(1) != family or candidate_match.group(3) != suffix:
                continue
            if int(candidate_match.group(2)) >= current_size:
                continue
            if self._validate_vm_price_candidate(item, arm_sku, os_type) is None:
                discovered.add(arm_sku)
        return sorted(discovered, key=lambda sku: int(re.fullmatch(r"(Standard_[A-Za-z]+?)(\d+)(.*)", sku).group(2)))

    # =========================================================
    # VM PRICE
    # =========================================================

    def get_vm_price(
        self,
        region: str,
        sku: str,
        os_type: str | None = None,
    ):
        """
        Resolve a standard PAYG VM price.

        Important:
        - Exact ARM SKU is required.
        - Spot pricing is rejected.
        - Low Priority pricing is rejected.
        - Reservation pricing is rejected.
        - Savings Plan pricing is rejected.
        - Dev/Test pricing is rejected.
        - OS-specific pricing is validated.
        """

        region = (
            region
            .lower()
            .strip()
        )

        sku = (
            sku
            .strip()
        )

        print(
            "\n[VM PRICE RESOLUTION]"
        )

        print(
            f"Region : {region}"
        )

        print(
            f"SKU    : {sku}"
        )

        print(
            f"OS     : {os_type}"
        )

        filters = [
            "serviceName eq 'Virtual Machines'",
            "priceType eq 'Consumption'",
            f"armRegionName eq "
            f"'{self._escape(region)}'",
            f"armSkuName eq "
            f"'{self._escape(sku)}'",
        ]

        filter_expression = (
            " and ".join(filters)
        )

        cache_key = (
            "virtual machines",
            region,
            sku.lower(),
            "",
            "Consumption",
        )
        items = self._get_cached_items(cache_key, filter_expression)

        if not items:

            print(
                "❌ No VM retail pricing found"
            )

            return None

        valid = []

        rejected = []

        for item in items:

            reason = (
                self._validate_vm_price_candidate(
                    item=item,
                    requested_sku=sku,
                    os_type=os_type,
                )
            )

            if reason is None:

                valid.append(item)

            else:

                rejected.append(
                    {
                        "item": item,
                        "reason": reason,
                    }
                )

                print(
                    "Rejected VM price candidate: "
                    f"{reason}"
                )

        if not valid:

            print(
                "❌ No valid standard VM pricing "
                "candidate found"
            )

            return None

        selected = (
            self._select_standard_vm_price(
                valid
            )
        )

        if selected is None:

            return None

        normalized = (
            self._normalize_item(
                selected
            )
        )

        normalized.update(
            {
                "pricing_validated": True,

                "pricing_selection":
                    "standard_payg",

                "requested_arm_sku":
                    sku,

                "rejected_candidate_count":
                    len(rejected),

                "pricing_warning":
                    None,
            }
        )

        print(
            "\n✅ Standard VM pricing selected"
        )

        print(
            f"ARM SKU : "
            f"{selected.get('armSkuName')}"
        )

        print(
            f"SKU     : "
            f"{selected.get('skuName')}"
        )

        print(
            f"Meter   : "
            f"{selected.get('meterName')}"
        )

        print(
            f"Price   : "
            f"{selected.get('retailPrice')}"
        )

        print(
            f"Rejected candidates: "
            f"{len(rejected)}"
        )

        return normalized

    # =========================================================
    # MANAGED DISK
    # =========================================================

    def get_managed_disk_price(
        self,
        region: str,
        disk_sku: str,
        disk_size_gb: int,
    ):

        region = (
            region
            .lower()
            .strip()
        )

        disk_sku = (
            disk_sku
            .strip()
        )

        print(
            "\n[Managed Disk Price Resolution]"
        )

        print(
            f"Region     : {region}"
        )

        print(
            f"ARM SKU    : {disk_sku}"
        )

        print(
            f"Size       : {disk_size_gb} GB"
        )

        tier = self._resolve_disk_tier(
            disk_sku=disk_sku,
            disk_size_gb=disk_size_gb,
        )

        if not tier:

            print(
                f"❌ Unsupported managed disk SKU: "
                f"{disk_sku}"
            )

            return None

        print(
            f"Pricing tier: {tier}"
        )

        storage_sku = self._storage_sku(
            disk_sku=disk_sku,
            tier=tier,
        )

        print(
            f"\nTrying Storage SKU: "
            f"{storage_sku}"
        )

        price = self.get_retail_price(
            service_name="Storage",
            region=region,
            sku_name=storage_sku,
        )

        if not price:

            print(
                f"❌ No Storage price found "
                f"for {storage_sku}"
            )

            return None

        returned_sku = str(
            price.get("sku_name") or ""
        ).upper().strip()

        expected_sku = (
            storage_sku
            .upper()
            .strip()
        )

        if returned_sku != expected_sku:

            print(
                "❌ Pricing SKU mismatch"
            )

            print(
                f"Expected: {expected_sku}"
            )

            print(
                f"Returned: {returned_sku}"
            )

            return None

        print(
            "\n✅ Managed Disk price found"
        )

        print(
            f"Pricing SKU : "
            f"{price.get('sku_name')}"
        )

        print(
            f"Price       : "
            f"{price.get('retail_price')}"
        )

        print(
            f"Unit        : "
            f"{price.get('unit_of_measure')}"
        )

        print(
            f"Meter       : "
            f"{price.get('meter_name')}"
        )

        price["disk_tier"] = tier

        price["storage_sku"] = storage_sku

        price["disk_size_gb"] = (
            disk_size_gb
        )

        return price

    # =========================================================
    # DISK TIER RESOLUTION
    # =========================================================

    @staticmethod
    def _resolve_disk_tier(
        disk_sku: str,
        disk_size_gb: int,
    ):

        sku = (
            disk_sku
            .upper()
            .strip()
        )

        if disk_size_gb <= 0:

            return None

        if sku == "PREMIUM_LRS":

            if disk_size_gb <= 128:
                return "P10"

            if disk_size_gb <= 512:
                return "P20"

            if disk_size_gb <= 1024:
                return "P30"

            if disk_size_gb <= 2048:
                return "P40"

            if disk_size_gb <= 4096:
                return "P50"

            if disk_size_gb <= 8192:
                return "P60"

            if disk_size_gb <= 16384:
                return "P70"

            if disk_size_gb <= 32767:
                return "P80"

            return None

        if sku == "STANDARDSSD_LRS":

            if disk_size_gb <= 128:
                return "E10"

            if disk_size_gb <= 256:
                return "E15"

            if disk_size_gb <= 512:
                return "E20"

            if disk_size_gb <= 1024:
                return "E30"

            if disk_size_gb <= 2048:
                return "E40"

            if disk_size_gb <= 4095:
                return "E50"

            if disk_size_gb <= 8191:
                return "E60"

            if disk_size_gb <= 16383:
                return "E70"

            if disk_size_gb <= 32767:
                return "E80"

            return None

        if sku == "STANDARD_LRS":

            if disk_size_gb <= 32:
                return "S4"

            if disk_size_gb <= 64:
                return "S6"

            if disk_size_gb <= 128:
                return "S10"

            if disk_size_gb <= 256:
                return "S15"

            if disk_size_gb <= 512:
                return "S20"

            if disk_size_gb <= 1024:
                return "S30"

            if disk_size_gb <= 2048:
                return "S40"

            if disk_size_gb <= 4095:
                return "S50"

            if disk_size_gb <= 8191:
                return "S60"

            if disk_size_gb <= 16383:
                return "S70"

            if disk_size_gb <= 32767:
                return "S80"

            return None

        return None

    # =========================================================
    # STORAGE SKU
    # =========================================================

    @staticmethod
    def _storage_sku(
        disk_sku: str,
        tier: str,
    ):

        return f"{tier} LRS"

    # =========================================================
    # HTTP PAGINATION
    # =========================================================

    def _get_all_items(
        self,
        filter_expression: str,
    ):

        items = []

        url = self.BASE_URL

        params = {
            "$filter": filter_expression
        }

        page = 1

        while url:
            response = self._get_with_retry(url, params)
            if response is None:
                return []

            response.raise_for_status()

            data = response.json()

            page_items = data.get(
                "Items",
                []
            )

            items.extend(
                page_items
            )

            print(
                f"Retail API page {page}: "
                f"{len(page_items)} items"
            )

            next_link = (
                data.get("NextPageLink")
                or data.get("nextPageLink")
            )

            if next_link:

                url = next_link

                params = None

                page += 1

            else:

                url = None

        return items

    def _get_cached_items(self, cache_key, filter_expression):
        if cache_key not in self._items_cache:
            self._items_cache[cache_key] = self._get_all_items(filter_expression)
        return self._items_cache[cache_key]

    def _get_with_retry(self, url, params):
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = self.session.get(url, params=params, timeout=30)
            except requests.RequestException:
                if attempt >= self.MAX_RETRIES:
                    return None
                self._sleep_before_retry(attempt, None)
                continue

            if response.status_code != 429:
                return response

            if attempt >= self.MAX_RETRIES:
                print("Retail API throttled after maximum retries")
                return None

            self._sleep_before_retry(attempt, response.headers.get("Retry-After"))

        return None

    def _sleep_before_retry(self, attempt, retry_after):
        delay = self._retry_after_seconds(retry_after)
        if delay is None:
            delay = self.RETRY_BASE_SECONDS * (2 ** attempt)
        delay += random.uniform(0, min(1.0, delay * 0.25))
        time.sleep(delay)

    @staticmethod
    def _retry_after_seconds(value):
        if value is None:
            return None
        try:
            return max(0.0, float(value))
        except (TypeError, ValueError):
            try:
                retry_at = parsedate_to_datetime(value)
                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=timezone.utc)
                return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
            except (TypeError, ValueError, OverflowError):
                return None

    # =========================================================
    # STANDARD VM SELECTION
    # =========================================================

    @classmethod
    def _select_standard_vm_price(
        cls,
        items: list[dict],
    ):

        if not items:

            return None

        candidates = []

        for item in items:

            score = 0

            combined = " ".join(
                [
                    str(
                        item.get("meterName")
                        or ""
                    ),
                    str(
                        item.get("skuName")
                        or ""
                    ),
                    str(
                        item.get("productName")
                        or ""
                    ),
                ]
            ).lower()

            if "low priority" not in combined:
                score += 100

            if "lowpriority" not in combined:
                score += 100

            if "spot" not in combined:
                score += 100

            if "reserved" not in combined:
                score += 50

            if "reservation" not in combined:
                score += 50

            if "savings plan" not in combined:
                score += 50

            if "savingsplan" not in combined:
                score += 50

            if "dev/test" not in combined:
                score += 25

            if "devtest" not in combined:
                score += 25

            if (
                item.get(
                    "isPrimaryMeterRegion"
                ) is True
            ):

                score += 10

            price = cls._safe_float(
                item.get("retailPrice")
            )

            if price > 0:

                score += 5

            candidates.append(
                (
                    score,
                    item
                )
            )

        candidates.sort(
            key=lambda x: (
                -x[0],

                cls._safe_float(
                    x[1].get(
                        "retailPrice"
                    )
                ),

                str(
                    x[1].get(
                        "meterName"
                    )
                    or ""
                ),
            )
        )

        return candidates[0][1]

    # =========================================================
    # GENERIC BEST ITEM
    # =========================================================

    @staticmethod
    def _select_best_item(
        items: list[dict],
        exclude_spot: bool = False,
    ):

        if not items:

            return None

        candidates = list(items)

        if exclude_spot:

            non_spot = [
                item
                for item in candidates
                if not AzureRetailPriceService._is_spot_item(
                    item
                )
            ]

            if non_spot:

                candidates = non_spot

        primary = [
            item
            for item in candidates
            if item.get(
                "isPrimaryMeterRegion"
            ) is True
        ]

        if primary:

            candidates = primary

        positive = [
            item
            for item in candidates
            if AzureRetailPriceService._safe_float(
                item.get("retailPrice")
            ) > 0
        ]

        if positive:

            candidates = positive

        candidates.sort(
            key=lambda item: (
                AzureRetailPriceService._is_spot_item(
                    item
                ),

                not bool(
                    item.get(
                        "isPrimaryMeterRegion"
                    )
                ),

                AzureRetailPriceService._safe_float(
                    item.get("retailPrice")
                ) <= 0,
            )
        )

        return candidates[0]

    # =========================================================
    # VM CANDIDATE VALIDATION
    # =========================================================

    @classmethod
    def _validate_vm_price_candidate(
        cls,
        item: dict,
        requested_sku: str,
        os_type: str | None = None,
    ):

        arm_sku = cls._normalize_text(
            item.get("armSkuName")
        )

        sku_name = cls._normalize_text(
            item.get("skuName")
        )

        meter_name = cls._normalize_text(
            item.get("meterName")
        )

        product_name = cls._normalize_text(
            item.get("productName")
        )

        requested = cls._normalize_text(
            requested_sku
        )

        combined = " ".join(
            [
                arm_sku,
                sku_name,
                meter_name,
                product_name,
            ]
        )

        # -----------------------------------------------------
        # Exact ARM SKU
        # -----------------------------------------------------

        if arm_sku != requested:

            return (
                f"ARM SKU mismatch: "
                f"{arm_sku!r} != "
                f"{requested!r}"
            )

        # -----------------------------------------------------
        # Pricing type exclusions
        # -----------------------------------------------------

        if "spot" in combined:

            return "Spot pricing"

        if (
            "low priority" in combined
            or "lowpriority" in combined
        ):

            return "Low Priority pricing"

        if (
            "dev/test" in combined
            or "devtest" in combined
        ):

            return "Dev/Test pricing"

        if "reservation" in combined:

            return "Reservation pricing"

        if "reserved" in combined:

            return "Reserved pricing"

        if (
            "savings plan" in combined
            or "savingsplan" in combined
        ):

            return "Savings Plan pricing"

        # -----------------------------------------------------
        # Price validation
        # -----------------------------------------------------

        price = cls._safe_float(
            item.get("retailPrice")
        )

        if price <= 0:

            return "Zero or negative price"

        # -----------------------------------------------------
        # OS validation
        # -----------------------------------------------------

        normalized_os = cls._normalize_text(
            os_type
        )

        if normalized_os == "linux":

            if (
                "windows" in combined
                or "win" in combined
            ):

                return (
                    "Windows price for Linux VM"
                )

        if normalized_os == "windows":

            if (
                "linux" in combined
                and "windows" not in combined
            ):

                return (
                    "Linux price for Windows VM"
                )

        return None

    # =========================================================
    # SPOT DETECTION
    # =========================================================

    @staticmethod
    def _is_spot_item(
        item: dict
    ):

        fields = [
            item.get("meterName"),
            item.get("skuName"),
            item.get("productName"),
            item.get("armSkuName"),
        ]

        text = " ".join(
            str(value or "")
            for value in fields
        ).lower()

        return "spot" in text

    # =========================================================
    # NORMALIZATION
    # =========================================================

    @staticmethod
    def _normalize_item(
        item: dict
    ):

        return {

            "retail_price":
                float(
                    item.get(
                        "retailPrice",
                        0
                    )
                ),

            "unit_of_measure":
                item.get(
                    "unitOfMeasure"
                ),

            "currency":
                item.get(
                    "currencyCode",
                    "USD"
                ),

            "meter_name":
                item.get(
                    "meterName"
                ),

            "sku_name":
                item.get(
                    "skuName"
                ),

            "arm_sku_name":
                item.get(
                    "armSkuName"
                ),

            "product_name":
                item.get(
                    "productName"
                ),

            "region":
                item.get(
                    "armRegionName"
                ),

            "service_name":
                item.get(
                    "serviceName"
                ),

            "service_family":
                item.get(
                    "serviceFamily"
                ),

            "unit_price":
                float(
                    item.get(
                        "retailPrice",
                        0
                    )
                ),

            "is_spot":
                AzureRetailPriceService._is_spot_item(
                    item
                ),

            "is_primary_meter_region":
                bool(
                    item.get(
                        "isPrimaryMeterRegion"
                    )
                ),

            "pricing_validated":
                False,

            "pricing_warning":
                None,
        }

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _safe_float(
        value
    ):

        try:

            return float(value)

        except (
            TypeError,
            ValueError,
        ):

            return 0.0

    @staticmethod
    def _escape(
        value: str
    ):

        return str(
            value
        ).replace(
            "'",
            "''"
        )

    @staticmethod
    def _normalize_text(
        value
    ):

        return (
            str(value or "")
            .strip()
            .lower()
        )