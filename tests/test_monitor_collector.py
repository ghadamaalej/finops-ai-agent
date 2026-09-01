from app.Collectors.resource_collector import ResourceCollector
from app.Collectors.monitor_collector import MonitorCollector


SUBSCRIPTION_ID = (
    "6850d94e-3234-463d-aa51-615d3c486939"
)


def main():

    print()
    print("=" * 70)
    print("MONITOR COLLECTOR TEST")
    print("=" * 70)

    resources = ResourceCollector().collect(
        SUBSCRIPTION_ID
    )

    collector = MonitorCollector()

    metrics = collector.collect(
        resources
    )

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)

    for metric in metrics:

        print()
        print(
            f"Resource ID : "
            f"{metric['resource_id']}"
        )

        print(
            f"CPU average : "
            f"{metric['cpu_average']}"
        )

        print(
            f"CPU max     : "
            f"{metric['cpu_max']}"
        )

        print(
            f"Days        : "
            f"{metric['collected_days']}"
        )

    collector.close()

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()