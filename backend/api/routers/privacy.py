from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

PRIVACY_PAGES_DIRECTORY = Path(__file__).parents[2] / "static" / "privacy"
SUPPORTED_PRIVACY_LOCALES = frozenset({"ca", "es", "en"})
PRIVACY_RESPONSE_HEADERS = {"Cache-Control": "public, max-age=3600"}

router = APIRouter(include_in_schema=False)


def load_privacy_page(locale: str) -> FileResponse:
    normalized_locale = locale.lower()
    if normalized_locale not in SUPPORTED_PRIVACY_LOCALES:
        raise HTTPException(status_code=404, detail="Idioma no disponible")
    return FileResponse(
        PRIVACY_PAGES_DIRECTORY / f"{normalized_locale}.html",
        media_type="text/html; charset=utf-8",
        headers={
            **PRIVACY_RESPONSE_HEADERS,
            "Content-Language": normalized_locale,
        },
    )


@router.get("/privacy")
def privacy() -> FileResponse:
    return load_privacy_page("ca")


@router.get("/privacy/{locale}")
def localized_privacy(locale: str) -> FileResponse:
    return load_privacy_page(locale)
