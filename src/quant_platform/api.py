from fastapi import FastAPI

from . import __version__
from .settings import settings

app = FastAPI(title="Quant Trading Platform", version=__version__)


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "version": __version__,
        "environment": settings.app_env,
        "paper_trading": settings.paper_trading,
    }
