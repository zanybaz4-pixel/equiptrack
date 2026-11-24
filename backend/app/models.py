"""ORM mapping; migrations, rather than create_all(), own PostgreSQL constraints."""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Identity, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(16))
    borrower_type: Mapped[str | None] = mapped_column(String(16))
    is_active: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PasswordResetLimit(Base):
    __tablename__ = "password_reset_limits"
    email_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer)


class Category(Base):
    __tablename__ = "equipment_categories"
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    description: Mapped[str] = mapped_column(Text)


class EquipmentItem(Base):
    __tablename__ = "equipment_items"
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("equipment_categories.id"))
    asset_code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(120))
    condition: Mapped[str] = mapped_column(String(16))
    service_status: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class BorrowingRequest(Base):
    __tablename__ = "borrowing_requests"
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    borrower_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment_items.id"))
    borrow_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    purpose: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(16))
    decided_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_remarks: Mapped[str | None] = mapped_column(String(500))
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class LoanRecord(Base):
    __tablename__ = "loan_records"
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("borrowing_requests.id"), unique=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment_items.id"))
    released_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    released_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    release_condition: Mapped[str] = mapped_column(String(16))
    returned_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    return_condition: Mapped[str | None] = mapped_column(String(16))
    return_remarks: Mapped[str | None] = mapped_column(String(500))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(40))
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[int] = mapped_column(BigInteger)
    details: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
