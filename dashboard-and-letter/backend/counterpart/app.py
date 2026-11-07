from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config, db
from .llm.client import LLMClient
from .routes import router
from .service import World


def create_app(db_path=None, client: LLMClient | None = None) -> FastAPI:
    app = FastAPI(title="Counterpart", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    conn = db.connect(db_path or config.DB_PATH)
    db.init_db(conn)
    app.state.db = conn
    app.state.world = World(conn, client)
    app.include_router(router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
