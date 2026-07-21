"""Expose the provider-neutral FastAPI application to Vercel's Python runtime."""

from backend.app import app

__all__ = ["app"]
