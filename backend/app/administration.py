from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query
from sqlalchemy import delete, func, select, text

from app.catalog import catalog_query
from app.db import DB
from app.lending import active_loan, lock_item
from app.lending_schemas import (
    AccountCreate, AccountUpdate, AuditOut, CategoryIn, DashboardOut,
    EquipmentIn, ProfileIn, UserOut,
)
from app.models import AuditLog, AuthSession, BorrowingRequest, Category, EquipmentItem, LoanRecord, User
from app.schemas import CategoryOut, EquipmentOut, errors
from app.security import Admin, AdminWriter, Current, Writer, hasher
from app.transactions import audit, persist

router = APIRouter(prefix="/api", tags=["administration"])
ResourceId = Annotated[int, Path(gt=0, le=2**63 - 1)]
READS = errors(401, 403, 422, 500, 503)
WRITES = errors(400, 401, 403, 404, 409, 422, 500, 503)


@router.get("/profile", response_model=UserOut, responses=errors(401, 500, 503))
def profile(principal: Current):
    return principal.user


@router.patch("/profile", response_model=UserOut, responses=WRITES)
def update_profile(body: ProfileIn, db: DB, principal: Writer):
    user = principal.user
    user.full_name = body.full_name
    audit(db, user.id, "profile.updated", "user", user.id)
    result = UserOut.model_validate(user)
    db.commit()
    return result


@router.get("/users", response_model=list[UserOut], responses=READS)
def list_users(db: DB, principal: Admin, offset: int = Query(0, ge=0, le=100000),
               limit: int = Query(25, ge=1, le=100)):
    return db.scalars(select(User).order_by(User.id).offset(offset).limit(limit)).all()


@router.post("/users", status_code=201, response_model=UserOut, responses=WRITES)
def create_user(body: AccountCreate, db: DB, principal: AdminWriter):
    user = User(**body.model_dump(exclude={"password"}), password_hash=hasher.hash(body.password),
                is_active=True, created_at=datetime.now(UTC))
    db.add(user)
    persist(db)
    audit(db, principal.user.id, "user.created", "user", user.id, role=user.role)
    result = UserOut.model_validate(user)
    db.commit()
    return result


@router.put("/users/{user_id}", response_model=UserOut, responses=WRITES)
def update_user(user_id: ResourceId, body: AccountUpdate, db: DB, principal: AdminWriter):
    # Serialize administrator changes and recheck the acting administrator after waiting.
    db.execute(text("SELECT pg_advisory_xact_lock(320347, 1)"))
    actor = db.get(User, principal.user.id, populate_existing=True)
    if not actor.is_active or actor.role != "admin":
        raise HTTPException(403, "Your role cannot perform this action.")
    user = db.get(User, user_id, with_for_update=True, populate_existing=True)
    if user is None:
        raise HTTPException(404, "Account not found.")
    if user.id == actor.id and (not body.is_active or body.role != "admin"):
        raise HTTPException(409, "You cannot deactivate or demote your own administrator account.")
    role_changed = user.role != body.role
    revoke_sessions = role_changed or not body.is_active
    for field, value in body.model_dump().items():
        setattr(user, field, value)
    if revoke_sessions:
        db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    audit(db, actor.id, "user.updated", "user", user.id, role=user.role, is_active=user.is_active)
    result = UserOut.model_validate(user)
    db.commit()
    return result


@router.post("/categories", status_code=201, response_model=CategoryOut, responses=WRITES)
def create_category(body: CategoryIn, db: DB, principal: AdminWriter):
    category = Category(**body.model_dump())
    db.add(category)
    persist(db)
    audit(db, principal.user.id, "category.created", "category", category.id)
    result = CategoryOut(id=category.id, name=category.name, description=category.description)
    db.commit()
    return result


def save_equipment(db: DB, item: EquipmentItem, actor_id: int, action: str):
    persist(db)
    audit(db, actor_id, action, "equipment", item.id, service_status=item.service_status)
    row = db.execute(catalog_query().where(EquipmentItem.id == item.id)).mappings().one()
    result = EquipmentOut.model_validate(row)
    db.commit()
    return result


@router.post("/equipment", status_code=201, response_model=EquipmentOut, responses=WRITES)
def create_equipment(body: EquipmentIn, db: DB, principal: AdminWriter):
    if db.get(Category, body.category_id) is None:
        raise HTTPException(404, "Equipment category not found.")
    item = EquipmentItem(**body.model_dump(), created_at=datetime.now(UTC))
    db.add(item)
    return save_equipment(db, item, principal.user.id, "equipment.created")


@router.put("/equipment/{equipment_id}", response_model=EquipmentOut, responses=WRITES)
def update_equipment(equipment_id: ResourceId, body: EquipmentIn, db: DB, principal: AdminWriter):
    item = lock_item(db, equipment_id)
    if db.get(Category, body.category_id) is None:
        raise HTTPException(404, "Equipment category not found.")
    changing_custody_fields = (item.service_status, item.condition) != (body.service_status, body.condition)
    if changing_custody_fields and active_loan(db, item.id) is not None:
        raise HTTPException(409, "Record the return before changing condition or service status.")
    if body.service_status == "retired" and db.scalar(select(BorrowingRequest.id).where(
        BorrowingRequest.equipment_id == item.id, BorrowingRequest.status == "approved",
        BorrowingRequest.due_at > datetime.now(UTC),
    ).limit(1)) is not None:
        raise HTTPException(409, "This item still has an approved reservation.")
    for field, value in body.model_dump().items():
        setattr(item, field, value)
    return save_equipment(db, item, principal.user.id, "equipment.updated")


@router.get("/dashboard", response_model=DashboardOut, responses=errors(401, 500, 503))
def dashboard(db: DB, principal: Current):
    visible = []
    if principal.user.role == "borrower":
        visible.append(BorrowingRequest.borrower_id == principal.user.id)
    by_status = dict(db.execute(select(BorrowingRequest.status, func.count()).where(*visible)
                                .group_by(BorrowingRequest.status)).all())
    overdue = db.scalar(select(func.count()).select_from(BorrowingRequest).join(
        LoanRecord, LoanRecord.request_id == BorrowingRequest.id
    ).where(*visible, LoanRecord.returned_at.is_(None), BorrowingRequest.due_at < datetime.now(UTC)))
    return DashboardOut(requests_by_status=by_status, overdue=overdue)


@router.get("/audit-logs", response_model=list[AuditOut], responses=READS)
def audit_logs(db: DB, principal: Admin, entity_id: int | None = Query(None, gt=0, le=2**63 - 1),
               offset: int = Query(0, ge=0, le=100000), limit: int = Query(25, ge=1, le=100)):
    statement = select(AuditLog)
    if entity_id is not None:
        statement = statement.where(AuditLog.entity_id == entity_id)
    return db.scalars(statement.order_by(AuditLog.id.desc()).offset(offset).limit(limit)).all()
