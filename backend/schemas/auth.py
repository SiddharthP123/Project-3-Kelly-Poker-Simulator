from datetime import datetime

from pydantic import EmailStr, Field

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
    starting_bankroll: float
    created_at: datetime
