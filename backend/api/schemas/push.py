from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PushSubscriptionRequestSchema(BaseModel):
    device_token: str = Field(min_length=32, max_length=512)
    app_version: str = Field(default="", max_length=64)
    locale: str = Field(default="ca-ES", min_length=2, max_length=16)
    environment: Literal["development", "production"] | None = None

    @field_validator("device_token")
    @classmethod
    def validate_device_token(cls, value: str) -> str:
        normalized = value.strip().lower()
        if len(normalized) % 2 or any(
            character not in "0123456789abcdef" for character in normalized
        ):
            raise ValueError("El token APNs ha de ser hexadecimal")
        return normalized
