import time
from fastapi import APIRouter
from src.api.db import get_conn, ALL_TABLES

router = APIRouter(tags=["health"])
_start_time = time.time()
VERSION = "1.0.0"


@router.get("/health")
def health():
    """Server health check: DB row counts for all tables, uptime, version."""
    conn = get_conn()
    counts = {}
    try:
        for t in ALL_TABLES:
            counts[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        status = "ok"
    except Exception:
        status = "db_unavailable"
    finally:
        conn.close()
    return {"status": status, "db_row_counts": counts,
            "uptime_seconds": round(time.time() - _start_time, 1), "version": VERSION}
