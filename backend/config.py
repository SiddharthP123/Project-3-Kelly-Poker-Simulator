"""Typed application settings, read from environment variables (and a local
.env file in dev). Never hardcode connection strings or secrets directly in
code -- this is the one place that's allowed to know where they come from.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # Matches docker-compose.yml's default `db` service so local dev works
    # out of the box with no .env file present; override via .env for
    # anything else (a different local Postgres, a hosted dev DB, etc).
    database_url: str = 'postgresql://kelly_user:kelly_password@localhost:5432/kelly_poker'

    # Comma-separated list of allowed frontend origins for CORS. The React
    # dev server (Part 10) runs on localhost:3000 by default.
    cors_allowed_origins: str = 'http://localhost:3000'

    @property
    def cors_allowed_origins_list(self):
        return [origin.strip() for origin in self.cors_allowed_origins.split(',') if origin.strip()]


settings = Settings()
