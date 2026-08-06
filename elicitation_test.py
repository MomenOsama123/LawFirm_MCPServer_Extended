import asyncio

from mcp_server.tools import (
    accept_case,
    reject_case,
    assign_case_to_lawyer,
)


class FakeAcceptedResponse:
    def __init__(self, data):
        self.action = "accept"
        self.data = data


class FakeContext:

    async def enable_components(self, *args, **kwargs):
        """Mock method for MCP Context component enabling."""
        pass

    async def disable_components(self, *args, **kwargs):
        """Mock method for MCP Context component disabling."""
        pass

    async def report_progress(self, progress: float, total: float | None = None):
        """Mock method for MCP progress reporting."""
        pass

    async def info(self, message: str):
        print(f"[INFO] {message}")

    async def warn(self, message: str):
        print(f"[WARN] {message}")

    async def error(self, message: str):
        print(f"[ERROR] {message}")

    async def read_resource(self, uri: str):
        """Mock method for reading MCP resources."""
        return ""

    async def elicit(self, message, response_type=None, **kwargs):
        print("\n===== ELICITATION =====")
        print(message)

        print("Requested model:")
        print(response_type.model_json_schema())

        values = {}

        for field in response_type.model_fields:
            if field == "case_id":
                values[field] = "case-002"

            elif field == "decided_by":
                values[field] = "staff-002"

            elif field == "decision_reason":
                values[field] = "Provided through elicitation."

            elif field == "lawyer_id":
                values[field] = "lawyer-001"

            elif field == "assigned_by":
                values[field] = "staff-002"

            elif field == "role_on_case":
                values[field] = "lead"

        return FakeAcceptedResponse(response_type(**values))


async def main():

    ctx = FakeContext()

    print("\n==============================")
    print("ACCEPT CASE")
    print("==============================")

    result = await accept_case(
        ctx,
        case_id="case-002",
        decided_by="staff-002",
        decision_reason=None,
    )

    print(result)

    print("\n==============================")
    print("REJECT CASE")
    print("==============================")

    result = await reject_case(
        ctx,
        case_id="case-003",
        decided_by=None,
        decision_reason=None,
    )

    print(result)

    print("\n==============================")
    print("ASSIGN LAWYER")
    print("==============================")

    result = await assign_case_to_lawyer(
        ctx,
        case_id="case-002",
        lawyer_id=None,
        assigned_by=None,
    )

    print(result)


if __name__ == "__main__":
    asyncio.run(main())