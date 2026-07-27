"""FastAPI server — Sprint 6, Day 38-40. 16 endpoints across 8 routers.
Run with: uvicorn src.api.main:app --port 8000
Docs at: http://localhost:8000/docs
"""
import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.routers import health, companies, screener, sectors, peers, valuation, portfolio, documents

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nifty100_api")

app = FastAPI(title="Nifty 100 Financial Intelligence API", version="1.0.0",
              description="REST API for the Nifty 100 Financial Intelligence Platform")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 1)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)")
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Spec requires HTTP 400 for invalid query params; FastAPI's default is 422."""
    return JSONResponse(status_code=400, content={"detail": exc.errors()})


app.include_router(health.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(screener.router, prefix="/api/v1")
app.include_router(sectors.router, prefix="/api/v1")
app.include_router(peers.router, prefix="/api/v1")
app.include_router(valuation.router, prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "Nifty 100 Financial Intelligence API. See /docs for OpenAPI documentation."}
