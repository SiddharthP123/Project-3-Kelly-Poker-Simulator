"""Shared bases for request/response schemas.

ApiModel: extra='forbid' rejects unexpected fields on every REQUEST -- the
direct Pydantic equivalent of Zod's strict mode from the project's
standing security conventions. Not used for responses, since we control
our own output shape and "extra fields forbidden" has no security value
there.

OrmResponseModel: from_attributes=True lets a response schema be built
directly from a SQLAlchemy model instance (`Model.model_validate(row)`),
rather than manually copying each column into a dict first.
"""

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class OrmResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
