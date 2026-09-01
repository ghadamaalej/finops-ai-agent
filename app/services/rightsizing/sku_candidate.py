from azure.mgmt.compute import ComputeManagementClient


def get_available_sizes(
    compute_client,
    resource_group,
    vm_name,
):

    sizes = (
        compute_client
        .virtual_machines
        .list_available_sizes(
            resource_group,
            vm_name,
        )
    )

    return [
        {
            "name": size.name,
            "number_of_cores": (
                size.number_of_cores
            ),
            "memory_mb": (
                size.memory_in_mb
            ),
        }
        for size in sizes
    ]