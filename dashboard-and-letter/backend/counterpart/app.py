from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from . import config, db
from .llm.client import LLMClient
from .cases import CaseError, CaseService
from .routes import router
from .routes_cases import router as cases_router
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
    app.state.cases = CaseService(app.state.world)
    if not conn.execute("SELECT 1 FROM cases").fetchone():
        app.state.cases.seed()
    app.include_router(router)
    app.include_router(cases_router)

    @app.exception_handler(CaseError)
    def case_error(_: Request, e: CaseError):
        return JSONResponse({"detail": e.detail}, status_code=e.status)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
