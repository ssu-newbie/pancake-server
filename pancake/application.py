from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pancake.api import create_router
from pancake.storage import JsonStore


def create_app(data_dir: str | Path | None = None) -> FastAPI:
    """Build one app; an explicit data directory must already exist."""
    if data_dir is None:
        # Keep existing files beside pancake_server.py, regardless of cwd.
        data_dir = Path(__file__).resolve().parent.parent
    store = JsonStore(Path(data_dir))
    app = FastAPI(title="PancakE Survey Server", version="1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
    )
    app.include_router(create_router(store))
    return app
