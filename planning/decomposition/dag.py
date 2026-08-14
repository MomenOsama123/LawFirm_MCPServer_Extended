def validate_and_sort(tasks):
    by_id = {task["id"]: task for task in tasks}

    visiting = set()
    visited = set()
    order = []

    def visit(task_id):
        if task_id in visiting:
            raise ValueError(
                f"Cycle detected: dependency leads back to '{task_id}'"
            )

        if task_id in visited:
            return

        visiting.add(task_id)

        for dependency in by_id[task_id].get("depends_on", []):
            if dependency not in by_id:
                raise ValueError(
                    f"Unknown dependency: '{task_id}' depends on '{dependency}'"
                )

            visit(dependency)

        visiting.remove(task_id)
        visited.add(task_id)
        order.append(task_id)

    for task in tasks:
        visit(task["id"])

    return order