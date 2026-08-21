from typing import Any

from fastmcp import Context
from pydantic import BaseModel, Field, create_model


async def require_fields(
    ctx: Context,
    values: dict[str, Any],
    field_descriptions: dict[str, str],
) -> dict[str, Any]:
    """
    Ensure all required fields are present.

    If some are missing, use FastMCP's elicitation mechanism to ask
    the user only for those missing fields.
    """

    missing = {
        field: description
        for field, description in field_descriptions.items()
        if values.get(field) is None
        or (
            isinstance(values.get(field), str)
            and values[field].strip() == ""
        )
    }

    if not missing:
        return values

    # Dynamically build a Pydantic model with only the missing fields
    fields = {
        field: (
            str,
            Field(
                ...,
                description=description,
            ),
        )
        for field, description in missing.items()
    }

    ElicitationModel: type[BaseModel] = create_model(
        "MissingFields",
        **fields,
    )

    response = await ctx.elicit(
        message="Some required information is missing.",
        response_type=ElicitationModel,
    )

    if response.action != "accept":
        raise ValueError("User cancelled elicitation.")

    # response.data is a Pydantic model
    values.update(response.data.model_dump())

    return values