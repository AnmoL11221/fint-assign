from fastapi import APIRouter

from app import __version__

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
