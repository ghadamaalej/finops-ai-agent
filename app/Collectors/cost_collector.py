import random
import time
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from azure.identity import (
    AzureCliCredential,
    CredentialUnavailableError,
)

from azure.mgmt.costmanagement import CostManagementClient

from azure.mgmt.costmanagement.models import (
    QueryDefinition,
    QueryDataset,
    QueryAggregation,
    QueryGrouping,
    QueryTimePeriod,
)

from azure.core.exceptions import (
    HttpResponseError,
    ClientAuthenticationError,
    ServiceResponseError,
    ServiceRequestError,
)

from app.services.cost_calculator import (
    CostCalculator
)

class CostCollector:

    def __init__(self):

        self.credential = AzureCliCredential(
            process_timeout=30
        )

        self.client = CostManagementClient(
            credential=self.credential
        )

        # Cost Management is aggressively throttled.
        self.max_retries = 3

        # Prevent hammering the API during repeated tests.
        self.base_retry_seconds = 5


    def collect(
        self,
        subscription_id: str
    ) -> list[dict]:

        if not subscription_id:
            raise ValueError(
                "subscription_id is required"
            )

        scope = (
            f"/subscriptions/{subscription_id}"
        )

        end_date = datetime.now(
            timezone.utc
        ).date()

        start_date = (
            end_date - timedelta(days=30)
        )

        print()
        print("=" * 70)
        print("AZURE COST COLLECTION")
        print("=" * 70)

        print(
            f"Scope      : {scope}"
        )

        print(
            f"Start date : {start_date}"
        )

        print(
            f"End date   : {end_date}"
        )

        if not self._test_authentication():

            print(
                "Cost collection aborted because "
                "Azure authentication failed."
            )

            return []

        dataset = QueryDataset(

            granularity="None",

            aggregation={
                "totalCost": QueryAggregation(
                    name="PreTaxCost",
                    function="Sum"
                )
            },

            grouping=[
                QueryGrouping(
                    type="Dimension",
                    name="ResourceId"
                ),

                QueryGrouping(
                    type="Dimension",
                    name="ServiceName"
                )
            ]
        )

        parameters = QueryDefinition(

            type="Usage",

            timeframe="Custom",

            time_period=QueryTimePeriod(

                from_property=datetime.combine(
                    start_date,
                    datetime.min.time(),
                    tzinfo=timezone.utc
                ),

                to=datetime.combine(
                    end_date + timedelta(days=1),
                    datetime.min.time(),
                    tzinfo=timezone.utc
                )
            ),

            dataset=dataset
        )

        result = self._query_with_retry(
            scope,
            parameters
        )

        if result is None:

            print()
            print(
                "Cost Management query did not return "
                "a result."
            )

            return []

        print()
        print("Cost API columns:")

        for index, column in enumerate(
            result.columns
        ):

            print(
                f"  [{index}] "
                f"{column['name']}"
            )

        print(
            f"\nRows returned: "
            f"{len(result.rows)}"
        )

        if not result.rows:

            print()
            print("=" * 70)
            print("NO COST DATA")
            print("=" * 70)

            print(
                "Azure Cost Management successfully "
                "processed the query but returned "
                "zero rows."
            )

            print(
                "This is different from an API failure."
            )

            return []

        columns = [
            column["name"]
            for column in result.columns
        ]

        print()
        print("Resolved columns:")
        print(columns)

        resource_column = self._find_column(
            columns,
            "ResourceId"
        )

        cost_column = self._find_column(
            columns,
            "PreTaxCost"
        )

        service_column = self._find_column(
            columns,
            "ServiceName"
        )

        currency_column = self._find_column(
            columns,
            "Currency"
        )

        print()
        print(
            f"Resource column : {resource_column}"
        )

        print(
            f"Cost column     : {cost_column}"
        )

        print(
            f"Service column  : {service_column}"
        )

        print(
            f"Currency column : {currency_column}"
        )

        if not resource_column:

            raise RuntimeError(
                "Azure Cost Management response "
                "does not contain ResourceId."
            )

        if not cost_column:

            raise RuntimeError(
                "Azure Cost Management response "
                "does not contain PreTaxCost."
            )

        cost_by_resource = defaultdict(float)

        service_by_resource = {}

        currency_by_resource = {}

        for row in result.rows:

            item = dict(
                zip(
                    columns,
                    row
                )
            )

            raw_resource_id = item.get(
                resource_column
            )

            if not raw_resource_id:
                continue

            resource_id = (
                self.normalize_resource_id(
                    raw_resource_id
                )
            )

            if not resource_id:
                continue

            raw_cost = item.get(
                cost_column,
                0
            )

            try:

                cost = float(
                    raw_cost or 0
                )

            except (
                TypeError,
                ValueError
            ):

                cost = 0.0

            cost_by_resource[
                resource_id
            ] += cost

            if service_column:

                service = item.get(
                    service_column
                )

                if service:

                    service_by_resource[
                        resource_id
                    ] = service

            if currency_column:

                currency = item.get(
                    currency_column
                )

                if currency:

                    currency_by_resource[
                        resource_id
                    ] = currency

        costs = []

        for resource_id, cost in (
            cost_by_resource.items()
        ):

            resource_name = (
                resource_id.split("/")[-1]
            )

            currency = (
                currency_by_resource.get(
                    resource_id
                )
                or "USD"
            )

            cost_value = round(
                cost,
                4
            )

            costs.append({

                "resource_id":
                    resource_id,

                "resource_name":
                    resource_name,

                "service_name":
                    service_by_resource.get(
                        resource_id,
                        "Unknown"
                    ),

                "cost_last_30_days":
                    cost_value,

                "monthly_cost":
                    cost_value,

                "currency":
                    currency
            })

        costs.sort(
            key=lambda item:
                item["monthly_cost"],
            reverse=True
        )

        print()
        print(
            f"Collected cost data for "
            f"{len(costs)} resources."
        )

        positive_costs = [
            item
            for item in costs
            if item["monthly_cost"] > 0
        ]

        print(
            f"Resources with positive cost: "
            f"{len(positive_costs)}"
        )

        print()
        print("Top cost records:")

        for item in costs[:10]:

            print(
                f"  "
                f"{item['resource_name']:<35} "
                f"{item['monthly_cost']:>10.2f} "
                f"{item['currency']}"
            )

        print(
            "\n" + "=" * 70
        )

        return costs

    def _test_authentication(self):

        try:

            token = self.credential.get_token(
                "https://management.azure.com/.default"
            )

            print()
            print(
                "Azure authentication OK "
                f"(token length={len(token.token)})"
            )

            return True

        except CredentialUnavailableError as exc:

            print()
            print(
                "Azure CLI credential unavailable:"
            )

            print(exc)

            return False

        except ClientAuthenticationError as exc:

            print()
            print(
                "Azure authentication failed:"
            )

            print(exc)

            return False

        except Exception as exc:

            print()
            print(
                "Unexpected authentication error:"
            )

            print(
                f"{type(exc).__name__}: {exc}"
            )

            return False

    def _query_with_retry(
        self,
        scope,
        parameters
    ):

        for attempt in range(
            1,
            self.max_retries + 1
        ):

            try:

                print()

                print(
                    f"Calling Azure Cost Management API "
                    f"(attempt {attempt}/"
                    f"{self.max_retries})..."
                )

                result = (
                    self.client.query.usage(
                        scope=scope,
                        parameters=parameters
                    )
                )

                print(
                    "Azure Cost Management API succeeded."
                )

                return result

            except HttpResponseError as exc:

                status_code = (
                    getattr(
                        exc,
                        "status_code",
                        None
                    )
                )

                if status_code == 429:

                    if attempt >= self.max_retries:

                        print()
                        print(
                            "Cost Management API remains "
                            "rate limited after retries."
                        )

                        print(
                            "Do NOT continue retrying "
                            "immediately."
                        )

                        return None

                    wait = (
                        self._get_retry_after(
                            exc,
                            attempt
                        )
                    )

                    print(
                        "Azure Cost API HTTP 429:"
                    )

                    print(
                        "Too many requests."
                    )

                    print(
                        f"Waiting {wait:.1f}s "
                        "before retry..."
                    )

                    time.sleep(wait)

                    continue

                if status_code in (
                    500,
                    502,
                    503,
                    504
                ):

                    if attempt >= self.max_retries:

                        print(
                            "Cost Management service "
                            "remained unavailable."
                        )

                        return None

                    wait = (
                        self._calculate_backoff(
                            attempt
                        )
                    )

                    print(
                        f"Azure Cost API HTTP "
                        f"{status_code}."
                    )

                    print(
                        f"Retrying in {wait:.1f}s..."
                    )

                    time.sleep(wait)

                    continue

                print()
                print(
                    "Azure Cost API HTTP error:"
                )

                print(exc)

                return None

            except (
                ServiceResponseError,
                ServiceRequestError
            ) as exc:

                if attempt >= self.max_retries:

                    print(
                        "Azure Cost API connection "
                        "failed after retries."
                    )

                    return None

                wait = (
                    self._calculate_backoff(
                        attempt
                    )
                )

                print(
                    "Azure Cost API connection error:"
                )

                print(exc)

                print(
                    f"Retrying in {wait:.1f}s..."
                )

                time.sleep(wait)

        return None

    @staticmethod
    def _get_retry_after(
        exception,
        attempt
    ):

        try:

            response = getattr(
                exception,
                "response",
                None
            )

            if response:

                headers = getattr(
                    response,
                    "headers",
                    {}
                )

                # Standard header
                retry_after = headers.get(
                    "Retry-After"
                )

                if retry_after:

                    return min(
                        float(retry_after),
                        60.0
                    )

                # Azure Cost Management header
                retry_after = headers.get(
                    "x-ms-ratelimit-microsoft.consumption-retry-after"
                )

                if retry_after:

                    return min(
                        float(retry_after),
                        60.0
                    )

        except (
            TypeError,
            ValueError,
            AttributeError
        ):

            pass

        return min(
            60.0,
            (
                5 * (2 ** (attempt - 1))
            )
            + random.uniform(
                0,
                2
            )
        )

    @staticmethod
    def _calculate_backoff(
        attempt
    ):

        return min(
            60.0,
            (
                5 * (2 ** (attempt - 1))
            )
            + random.uniform(
                0,
                2
            )
        )

    @staticmethod
    def normalize_resource_id(
        resource_id
    ):

        if not resource_id:
            return None

        return (
            str(resource_id)
            .strip()
            .rstrip("/")
            .lower()
        )

    @staticmethod
    def _find_column(
        columns,
        expected_name
    ):

        for column in columns:

            if (
                column.lower()
                == expected_name.lower()
            ):

                return column

        return None