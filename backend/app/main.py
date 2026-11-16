import logging
from uuid import uuid4
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.catalog import catalog_query, list_equipment
from app import administration, auth, lending
from app.db import DB
from app.lending_schemas import BookingTimestamp
from app.models import Category, EquipmentItem
from app.schemas import Availability, CategoryOut, EquipmentOut, EquipmentPage, errors
from app.security import Current

logger = logging.getLogger("equiptrack")
app = FastAPI(
    title="EquipTrack API", version="0.2.0",
    description=("Synthetic equipment lending. Cookie-authenticated writes require the configured Origin "
                 "and the X-CSRF-Token returned by login or session lookup."),
    docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None,
)
app.include_router(auth.router)
app.include_router(lending.router)
app.include_router(administration.router)


@app.middleware("http")
async def response_headers(request: Request, call_next):
    request.state.request_id = str(uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response


def error(request: Request, status: int, code: str, message: str,
          headers: dict[str, str] | None = None):
    request_id = getattr(request.state, "request_id", str(uuid4()))
    return JSONResponse(status_code=status, content={"error": {
        "code": code, "message": message,
        "request_id": request_id,
    }}, headers={**(headers or {}), "X-Request-ID": request_id,
                 "X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"})


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    return error(request, exc.status_code, {
        400: "bad_request", 401: "unauthenticated", 403: "forbidden", 404: "not_found",
        405: "method_not_allowed", 409: "conflict", 422: "validation_error", 429: "rate_limited",
    }
                 .get(exc.status_code, "request_error"), str(exc.detail), exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    if any(item["type"] == "json_invalid" for item in exc.errors()):
        return error(request, 400, "bad_request", "The request body is not valid JSON.")
    return error(request, 422, "validation_error", "Invalid request parameters. Check the API schema.")


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError):
    # Never log exception text: it can contain credentials or user input.
    if isinstance(exc, OperationalError):
        logger.error("database_unavailable request_id=%s type=%s",
                     request.state.request_id, type(exc).__name__)
        return error(request, 503, "database_unavailable", "The database is temporarily unavailable.")
    return await unexpected_error(request, exc)


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    logger.error("internal_error request_id=%s type=%s",
                 getattr(request.state, "request_id", "unknown"), type(exc).__name__)
    return error(request, 500, "internal_error", "An unexpected error occurred.")


@app.get("/api/health/live", tags=["operations"], responses=errors(500))
def live():
    return {"status": "ok", "service": "equiptrack-api", "phase": 2}


@app.get("/api/health/ready", tags=["operations"], responses=errors(500, 503))
def ready(db: DB):
    db.execute(text("SELECT 1 FROM equipment_items, auth_sessions LIMIT 0"))
    return {"status": "ready", "database": "postgresql"}


@app.get("/api/categories", response_model=list[CategoryOut], tags=["availability"],
         responses=errors(401, 500, 503))
def categories(db: DB, principal: Current):
    rows = db.execute(select(Category.id, Category.name, Category.description)
                      .order_by(Category.name)).mappings().all()
    return [dict(row) for row in rows]


def booking_period(borrow_at: BookingTimestamp | None = None, due_at: BookingTimestamp | None = None):
    if borrow_at is None and due_at is None:
        return None, None
    if borrow_at is None or due_at is None or due_at <= borrow_at:
        raise HTTPException(422, "Specify a borrowing time and a later expected return time.")
    return borrow_at, due_at


Period = Annotated[tuple, Depends(booking_period)]


@app.get("/api/equipment", response_model=EquipmentPage, tags=["availability"],
         responses=errors(401, 422, 500, 503))
def equipment(db: DB, principal: Current, period: Period, q: str = Query("", max_length=120),
              category_id: int | None = Query(None, gt=0, le=2**63 - 1),
              availability: Availability | None = None,
              offset: int = Query(0, ge=0, le=100000), limit: int = Query(12, ge=1, le=100)):
    return list_equipment(db, q.strip(), category_id, availability, offset, limit, *period)


@app.get("/api/equipment/{equipment_id}", response_model=EquipmentOut, tags=["availability"],
         responses=errors(401, 404, 422, 500, 503))
def equipment_detail(db: DB, principal: Current, period: Period, equipment_id: int = Path(gt=0, le=2**63 - 1)):
    row = db.execute(catalog_query(start=period[0], end=period[1])
                     .where(EquipmentItem.id == equipment_id)).mappings().first()
    if row is None:
        raise HTTPException(404, "Equipment not found.")
    return dict(row)
