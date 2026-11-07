from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config, db


def create_app(db_path=None) -> FastAPI:
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

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
