from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from backend.schemas.base import ApiModel, OrmResponseModel


class SignupRequest(ApiModel):
    email: EmailStr
    # max_length=72 matches bcrypt's hard limit (see backend/security.py);
    # enforced here so an over-length password 422s cleanly instead of
    # raising inside the hashing call.
    password: str = Field(min_length=8, max_length=72)
    display_name: str | None = Field(default=None, max_length=100)
    starting_bankroll: float = Field(default=1000.0, gt=0)


class LoginRequest(ApiModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class TokenResponse(ApiModel):
    access_token: str
    token_type: str = 'bearer'


class UserResponse(OrmResponseModel):
    id: int
    email: str
    display_name: str | None
    bio: str | None
    avatar_url: str | None
    starting_bankroll: float
    created_at: datetime


class UpdateProfileRequest(ApiModel):
    """PATCH /auth/me's body -- a full-form save (the frontend's ProfilePage
    always submits all three fields together, not a partial patch of just
    one), so a field left blank in the form clears that column rather than
    leaving it untouched. blank_to_none turns an empty-string field (the
    natural "cleared" state of a text input) into a real NULL, rather than
    persisting an empty string that would render identically but compare
    differently (e.g. `bio is not None` checks elsewhere)."""

    display_name: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = Field(default=None, max_length=2048)

    @field_validator('display_name', 'bio', 'avatar_url', mode='before')
    @classmethod
    def blank_to_none(cls, value):
        if isinstance(value, str) and value.strip() == '':
            return None
        return value
