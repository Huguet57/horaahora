from typing import Literal

from pydantic import BaseModel, Field, field_validator

from backend.domain.notifications.interest import InterestLevel, group_key


class GroupSelectionSchema(BaseModel):
    mode: Literal["all", "custom"] = "all"
    keys: list[str] = Field(default_factory=list, max_length=500)

    @field_validator("keys")
    @classmethod
    def normalize_keys(cls, values: list[str]) -> list[str]:
        keys = sorted({group_key(value) for value in values})
        if any(not key or len(key) > 200 for key in keys):
            raise ValueError("Nom de colla no vàlid")
        return keys


class PushSubscriptionRequestSchema(BaseModel):
    device_token: str = Field(min_length=32, max_length=512)
    app_version: str = Field(default="", max_length=64)
    locale: str = Field(default="ca-ES", min_length=2, max_length=16)
    environment: Literal["development", "production"] | None = None
    minimum_interest: InterestLevel | None = None
    group_selection: GroupSelectionSchema | None = None

    @field_validator("device_token")
    @classmethod
    def validate_device_token(cls, value: str) -> str:
        normalized = value.strip().lower()
        if len(normalized) % 2 or any(
            character not in "0123456789abcdef" for character in normalized
        ):
            raise ValueError("El token APNs ha de ser hexadecimal")
        return normalized
