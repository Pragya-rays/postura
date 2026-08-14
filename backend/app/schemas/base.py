"""Every request/response schema subclasses CamelModel. Python-side attribute
names stay snake_case (matching SQLAlchemy model attributes, so
`SomeOut.model_validate(orm_row)` just works via from_attributes); the wire
format is camelCase via alias_generator, matching frontend/lib/types.ts
exactly. populate_by_name means request bodies can be constructed from
snake_case kwargs in code while still accepting camelCase JSON on the wire.
"""
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
