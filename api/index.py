"""Expose the provider-neutral FastAPI application to Vercel's Python runtime."""

from backend.app import create_app
from backend.config import Settings

app = create_app(Settings.from_env())

__all__ = ["app"]
