from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import AuditLog


def audit(db: Session, actor_id: int, action: str, entity_type: str, entity_id: int, **details):
    db.add(AuditLog(actor_id=actor_id, action=action, entity_type=entity_type,
                    entity_id=entity_id, details=details, created_at=datetime.now(UTC)))


def persist(db: Session):
    """Flush before serializing so identity fields and constraints are resolved."""
    try:
        db.flush()
    except IntegrityError as exc:
        name = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        conflicts = {
            "no_overlapping_reservations": "This equipment is already reserved for these dates. Choose another time or another item.",
            "one_active_loan_per_item": "This item is already checked out.",
            "loan_records_request_id_key": "This request already has a release record.",
            "users_email_key": "An account already uses that email address.",
            "equipment_items_asset_code_key": "An item already uses that asset code.",
            "equipment_categories_name_key": "A category already uses that name.",
        }
        if name not in conflicts:
            raise
        raise HTTPException(409, conflicts[name]) from exc
