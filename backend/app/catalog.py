from datetime import datetime, timezone

from sqlalchemy import case, exists, func, or_, select
from sqlalchemy.orm import Session

from app.models import BorrowingRequest, Category, EquipmentItem, LoanRecord


def availability_expression(now: datetime, start: datetime | None = None, end: datetime | None = None):
    active_loan = exists().where(
        LoanRecord.equipment_id == EquipmentItem.id,
        LoanRecord.returned_at.is_(None),
    )
    current_reservation = exists().where(
        BorrowingRequest.equipment_id == EquipmentItem.id,
        BorrowingRequest.status.in_(["approved", "released"]),
    )
    if start is None:
        current_reservation = current_reservation.where(
            BorrowingRequest.borrow_at <= now, BorrowingRequest.due_at > now
        )
    else:
        current_reservation = current_reservation.where(
            BorrowingRequest.borrow_at < end, BorrowingRequest.due_at > start
        )
        active_loan = active_loan.where(exists().where(
            BorrowingRequest.id == LoanRecord.request_id,
            or_(BorrowingRequest.due_at <= now, BorrowingRequest.due_at > start),
        ))
    return case(
        (EquipmentItem.service_status == "retired", "retired"),
        (EquipmentItem.service_status == "maintenance", "maintenance"),
        (active_loan, "on_loan"),
        (current_reservation, "reserved"),
        else_="available",
    ).label("availability")


def catalog_query(now: datetime | None = None, start: datetime | None = None, end: datetime | None = None):
    return select(
        EquipmentItem.id, EquipmentItem.asset_code, EquipmentItem.name,
        EquipmentItem.description, EquipmentItem.location, EquipmentItem.category_id,
        Category.name.label("category"), EquipmentItem.condition,
        availability_expression(now or datetime.now(timezone.utc), start, end),
    ).outerjoin(Category, Category.id == EquipmentItem.category_id)


def list_equipment(db: Session, q: str, category_id: int | None,
                   availability: str | None, offset: int, limit: int,
                   start: datetime | None = None, end: datetime | None = None):
    now = datetime.now(timezone.utc)
    query = catalog_query(now, start, end)
    if q:
        # Treat user '%' and '_' literally, not as wildcard operators.
        query = query.where(or_(
            EquipmentItem.name.icontains(q, autoescape=True),
            EquipmentItem.asset_code.icontains(q, autoescape=True),
        ))
    if category_id is not None:
        query = query.where(EquipmentItem.category_id == category_id)
    if availability is not None:
        query = query.where(availability_expression(now, start, end) == availability)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.execute(query.order_by(EquipmentItem.name, EquipmentItem.id)
                      .offset(offset).limit(limit)).mappings().all()
    return {"items": [dict(row) for row in rows], "total": total,
            "offset": offset, "limit": limit}
