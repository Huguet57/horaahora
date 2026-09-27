import re
from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.domain.notifications.interest import InterestLevel, group_key
from backend.domain.notifications.models import PushPlatform

# Firebase registration tokens: URL-safe base64 plus separators, case-sensitive.
_FCM_TOKEN = re.compile(r"[A-Za-z0-9_:.\-]+")


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
    # iOS builds that predate Android support do not send it.
    platform: PushPlatform = PushPlatform.IOS

    @model_validator(mode="after")
    def validate_device_token(self) -> Self:
        token = self.device_token.strip()
        if self.platform is PushPlatform.ANDROID:
            if not _FCM_TOKEN.fullmatch(token):
                raise ValueError("El token FCM no és vàlid")
            self.device_token = token
            return self
        normalized = token.lower()
        if len(normalized) % 2 or any(
            character not in "0123456789abcdef" for character in normalized
        ):
            raise ValueError("El token APNs ha de ser hexadecimal")
        self.device_token = normalized
        return self
