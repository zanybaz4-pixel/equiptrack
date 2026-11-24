from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Path, Query, Response
from sqlalchemy import literal, or_, select
from sqlalchemy.orm import Session

from app.db import DB
from app.lending_schemas import DecisionIn, LoanOut, ReleaseIn, RequestCreate, RequestOut, RequestStatus, ReturnIn, SearchText
from app.models import BorrowingRequest, EquipmentItem, LoanRecord, User
from app.schemas import errors
from app.security import AdminWriter, BorrowerWriter, Current
from app.transactions import audit, persist

router = APIRouter(prefix="/api/requests", tags=["borrowing"])
RequestId = Annotated[int, Path(gt=0, le=2**63 - 1)]
WRITES = errors(400, 401, 403, 404, 409, 422, 500, 503)


def active_loan(db: Session, equipment_id: int):
    return db.scalar(select(LoanRecord).where(
        LoanRecord.equipment_id == equipment_id, LoanRecord.returned_at.is_(None)
    ))


def lock_item(db: Session, equipment_id: int):
    item = db.scalar(select(EquipmentItem).where(EquipmentItem.id == equipment_id).with_for_update())
    if item is None:
        raise HTTPException(404, "Equipment not found.")
    return item


def check_serviceable(item: EquipmentItem):
    if item.service_status != "serviceable" or item.condition == "damaged":
        raise HTTPException(409, "This item is not serviceable.")


def check_reservation(db: Session, item: EquipmentItem, start: datetime, end: datetime, now: datetime):
    check_serviceable(item)
    overlap = db.scalar(select(BorrowingRequest.id).where(
        BorrowingRequest.equipment_id == item.id, BorrowingRequest.status.in_(("approved", "released")),
        BorrowingRequest.borrow_at < end, BorrowingRequest.due_at > start,
    ).limit(1))
    if overlap is not None:
        raise HTTPException(409, "This equipment is already reserved for these dates. Choose another time or another item.")
    loan = active_loan(db, item.id)
    if loan is not None:
        due = db.scalar(select(BorrowingRequest.due_at).where(BorrowingRequest.id == loan.request_id))
        if due <= now or start < due:
            raise HTTPException(409, "This item is checked out for the requested period.")


def visible_requests(user: User):
    statement = select(BorrowingRequest, EquipmentItem, LoanRecord).join(
        EquipmentItem, EquipmentItem.id == BorrowingRequest.equipment_id
    ).outerjoin(LoanRecord, LoanRecord.request_id == BorrowingRequest.id)
    if user.role == "borrower":
        return statement.where(BorrowingRequest.borrower_id == user.id).add_columns(literal(None))
    return statement.join(User, User.id == BorrowingRequest.borrower_id).add_columns(User.full_name)


def serialize_request(row: BorrowingRequest, item: EquipmentItem, loan: LoanRecord | None,
                      now: datetime, borrower_name: str | None = None):
    return RequestOut(
        id=row.id, borrower_id=row.borrower_id, borrower_name=borrower_name, equipment_id=row.equipment_id,
        borrow_at=row.borrow_at, due_at=row.due_at, purpose=row.purpose, status=row.status,
        decided_by=row.decided_by, decided_at=row.decided_at, decision_remarks=row.decision_remarks,
        canceled_at=row.canceled_at, created_at=row.created_at, equipment_name=item.name,
        asset_code=item.asset_code, equipment_state=item.service_status,
        storage_rack=item.storage_rack or item.asset_code,
        loan=LoanOut.model_validate(loan) if loan is not None else None,
        is_overdue=bool(loan and loan.returned_at is None and now > row.due_at),
        was_returned_late=bool(loan and loan.returned_at and loan.returned_at > row.due_at),
    )


def lock_request(db: Session, request_id: int, owner_id: int | None = None):
    statement = select(BorrowingRequest).where(BorrowingRequest.id == request_id)
    if owner_id is not None:
        statement = statement.where(BorrowingRequest.borrower_id == owner_id)
    equipment_id = db.scalar(statement.with_only_columns(BorrowingRequest.equipment_id))
    if equipment_id is None:
        raise HTTPException(404, "Borrowing request not found.")
    item = lock_item(db, equipment_id)
    row = db.scalar(statement.with_for_update())
    if row is None:
        raise HTTPException(404, "Borrowing request not found.")
    return row, item


def require_status(row: BorrowingRequest, status: str):
    if row.status != status:
        raise HTTPException(409, f"This action requires a {status} request.")


def save_request(db: Session, actor: User, row: BorrowingRequest, item: EquipmentItem,
                 action: str, now: datetime, loan: LoanRecord | None = None):
    persist(db)
    audit(db, actor.id, action, "request", row.id, status=row.status, equipment_id=item.id)
    result = serialize_request(row, item, loan, now)
    db.commit()
    return result


@router.get("", response_model=list[RequestOut], responses=errors(401, 422, 500, 503))
def list_requests(db: DB, principal: Current, status: RequestStatus | None = None,
                  custody: Literal["active", "overdue"] | None = None, q: SearchText = "",
                  offset: int = Query(0, ge=0, le=100000), limit: int = Query(25, ge=1, le=100)):
    now = datetime.now(UTC)
    statement = visible_requests(principal.user)
    if status is not None:
        statement = statement.where(BorrowingRequest.status == status)
    if custody is not None:
        statement = statement.where(LoanRecord.id.is_not(None), LoanRecord.returned_at.is_(None))
    if custody == "overdue":
        statement = statement.where(BorrowingRequest.due_at < now)
    if q.strip():
        statement = statement.where(or_(EquipmentItem.name.icontains(q.strip(), autoescape=True),
                                        EquipmentItem.asset_code.icontains(q.strip(), autoescape=True),
                                        EquipmentItem.storage_rack.icontains(q.strip(), autoescape=True),
                                        EquipmentItem.location.icontains(q.strip(), autoescape=True)))
    statement = statement.order_by(BorrowingRequest.created_at.desc(), BorrowingRequest.id.desc()).offset(offset).limit(limit)
    return [serialize_request(row, item, loan, now, borrower_name)
            for row, item, loan, borrower_name in db.execute(statement)]


@router.get("/{request_id}", response_model=RequestOut, responses=errors(401, 404, 422, 500, 503))
def request_detail(request_id: RequestId, db: DB, principal: Current):
    result = db.execute(visible_requests(principal.user).where(BorrowingRequest.id == request_id)).first()
    if result is None:
        raise HTTPException(404, "Borrowing request not found.")
    row, item, loan, borrower_name = result
    return serialize_request(row, item, loan, datetime.now(UTC), borrower_name)


@router.post("", status_code=201, response_model=RequestOut, responses=WRITES)
def create_request(body: RequestCreate, response: Response, db: DB, principal: BorrowerWriter):
    item = lock_item(db, body.equipment_id)
    now = datetime.now(UTC)
    if body.borrow_at < now:
        raise HTTPException(422, "Borrowing time must be in the future.")
    check_reservation(db, item, body.borrow_at, body.due_at, now)
    row = BorrowingRequest(**body.model_dump(), borrower_id=principal.user.id,
                           status="pending", created_at=now)
    db.add(row)
    result = save_request(db, principal.user, row, item, "request.created", now)
    response.headers["Location"] = f"/api/requests/{result.id}"
    return result


@router.delete("/{request_id}", response_model=RequestOut, responses=WRITES)
def cancel_request(request_id: RequestId, db: DB, principal: BorrowerWriter):
    row, item = lock_request(db, request_id, principal.user.id)
    require_status(row, "pending")
    now = datetime.now(UTC)
    row.status = "canceled"
    row.canceled_at = now
    return save_request(db, principal.user, row, item, "request.canceled", now)


@router.patch("/{request_id}/decision", response_model=RequestOut, responses=WRITES)
def decide_request(request_id: RequestId, body: DecisionIn, db: DB, principal: AdminWriter):
    row, item = lock_request(db, request_id)
    require_status(row, "pending")
    now = datetime.now(UTC)
    if body.decision == "approved":
        borrower = db.get(User, row.borrower_id)
        if not borrower.is_active or borrower.role != "borrower":
            raise HTTPException(409, "The requester is no longer an active borrower.")
        if row.due_at <= now:
            raise HTTPException(409, "The borrowing period has expired.")
        check_reservation(db, item, row.borrow_at, row.due_at, now)
    row.status = body.decision
    row.decided_by = principal.user.id
    row.decided_at = now
    row.decision_remarks = body.remarks
    return save_request(db, principal.user, row, item, f"request.{body.decision}", now)


@router.post("/{request_id}/release", status_code=201, response_model=RequestOut, responses=WRITES)
def release_equipment(request_id: RequestId, body: ReleaseIn, db: DB, principal: AdminWriter):
    row, item = lock_request(db, request_id)
    require_status(row, "approved")
    check_serviceable(item)
    borrower = db.get(User, row.borrower_id)
    if not borrower.is_active or borrower.role != "borrower":
        raise HTTPException(409, "The requester is no longer an active borrower.")
    now = datetime.now(UTC)
    if not row.borrow_at <= now < row.due_at:
        raise HTTPException(409, "Equipment can only be released during the approved period.")
    if active_loan(db, item.id) is not None:
        raise HTTPException(409, "This item is already checked out.")
    loan = LoanRecord(request_id=row.id, equipment_id=item.id, released_by=principal.user.id,
                      released_at=now, release_condition=body.condition)
    row.status = "released"
    item.condition = body.condition
    db.add(loan)
    return save_request(db, principal.user, row, item, "equipment.released", now, loan)


@router.put("/{request_id}/return", response_model=RequestOut, responses=WRITES)
def return_equipment(request_id: RequestId, body: ReturnIn, db: DB, principal: AdminWriter):
    row, item = lock_request(db, request_id)
    require_status(row, "released")
    loan = db.scalar(select(LoanRecord).where(
        LoanRecord.request_id == row.id, LoanRecord.returned_at.is_(None)
    ).with_for_update())
    if loan is None:
        raise HTTPException(409, "This request has no open loan.")
    now = datetime.now(UTC)
    loan.returned_by = principal.user.id
    loan.returned_at = now
    loan.return_condition = body.condition
    loan.return_remarks = body.remarks
    row.status = "returned"
    item.condition = body.condition
    if body.condition == "damaged":
        item.service_status = "maintenance"
    return save_request(db, principal.user, row, item, "equipment.returned", now, loan)
