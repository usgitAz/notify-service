"""
Base schema classes.

- `BaseSchema`: common config for ALL schemas.
- `BaseRequest`: for request bodies (extra="forbid").
- `BaseResponse`: for response bodies (from_attributes=True).
"""

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    Base for all schemas.

    - `str_strip_whitespace`: trims "  hello  " → "hello".
    - `validate_assignment`: validates on attribute set (not just init).
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class BaseRequest(BaseSchema):
    """
    Base for request bodies.

    `extra="forbid"` → reject unknown fields (catches typos).
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class BaseResponse(BaseSchema):
    """
    Base for response bodies.

    `from_attributes=True` → Pydantic reads from ORM object attributes,
    not just dicts. Enables `Model.model_validate(orm_obj)`.
    """

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )
