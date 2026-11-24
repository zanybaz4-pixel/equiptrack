import re
from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    AfterValidator, AwareDatetime, BaseModel, BeforeValidator, ConfigDict, Field,
    StringConstraints, field_validator, model_validator,
)

Role = Literal["admin", "borrower"]
BorrowerType = Literal["student", "faculty"]
Condition = Literal["good", "fair", "damaged"]
ServiceStatus = Literal["serviceable", "maintenance", "retired"]
RequestStatus = Literal["pending", "approved", "rejected", "canceled", "released", "returned"]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Remarks = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
PositiveId = Annotated[int, Field(gt=0, le=2**63 - 1)]

BOOKING_TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}"
    r"(?::[0-9]{2}(?:\.[0-9]{1,6})?)?(?:Z|[+-][0-9]{2}:[0-9]{2})"
)


def require_booking_timestamp(value):
    if not isinstance(value, str) or not BOOKING_TIMESTAMP.fullmatch(value):
        raise ValueError("Supply an ISO 8601 timestamp with Z or a timezone offset.")
    return value


BookingTimestamp = Annotated[AwareDatetime, BeforeValidator(require_booking_timestamp)]


def validate_email(value: str) -> str:
    value = value.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s.]+(?:\.[^@\s.]+)+", value):
        raise ValueError("Enter a valid email address.")
    return value


Email = Annotated[str, StringConstraints(max_length=254), AfterValidator(validate_email)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def valid_database_text(cls, value):
        if isinstance(value, str):
            if "\x00" in value:
                raise ValueError("Null characters are not supported.")
            value.encode("utf-8")
        return value


class LoginIn(Input):
    email: Email
    password: Annotated[str, StringConstraints(min_length=1, max_length=128)] = Field(repr=False)


class PasswordResetRequestIn(Input):
    email: Email


class PasswordResetIn(Input):
    token: Annotated[str, StringConstraints(min_length=43, max_length=43, pattern=r"^[A-Za-z0-9_-]{43}$")] = Field(repr=False)
    password: Annotated[str, StringConstraints(min_length=12, max_length=128)] = Field(repr=False)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str
    role: Role
    borrower_type: BorrowerType | None
    is_active: bool


class SessionOut(BaseModel):
    user: UserOut
    csrf_token: str


class ProfileIn(Input):
    full_name: Name


class AccountFields(Input):
    full_name: Name
    role: Role
    borrower_type: BorrowerType | None = None

    @model_validator(mode="after")
    def check_role(self):
        if (self.role == "borrower") != (self.borrower_type is not None):
            raise ValueError("Specify student or faculty for borrower accounts only.")
        return self


class AccountCreate(AccountFields):
    email: Email
    password: Annotated[str, StringConstraints(min_length=12, max_length=128)] = Field(repr=False)


class AccountUpdate(AccountFields):
    is_active: bool


class CategoryIn(Input):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
    description: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] = ""


class EquipmentIn(Input):
    category_id: PositiveId
    asset_code: Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=1, max_length=40)]
    name: Name
    location: Name
    description: Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] = ""
    condition: Condition
    service_status: ServiceStatus

    @model_validator(mode="after")
    def check_damage(self):
        if self.condition == "damaged" and self.service_status == "serviceable":
            raise ValueError("Damaged equipment cannot be marked serviceable.")
        return self


class RequestCreate(Input):
    equipment_id: PositiveId
    borrow_at: BookingTimestamp
    due_at: BookingTimestamp
    purpose: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=500)]

    @model_validator(mode="after")
    def check_period(self):
        if self.due_at <= self.borrow_at:
            raise ValueError("Expected return must be after the borrowing time.")
        return self


class DecisionIn(Input):
    decision: Literal["approved", "rejected"]
    remarks: Remarks | None = None


class ReleaseIn(Input):
    condition: Literal["good", "fair"]


class ReturnIn(Input):
    condition: Condition
    remarks: Remarks | None = None


class LoanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    released_by: int
    released_at: datetime
    release_condition: Condition
    returned_by: int | None
    returned_at: datetime | None
    return_condition: Condition | None
    return_remarks: str | None


class RequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    borrower_id: int
    borrower_name: str | None = None
    equipment_id: int
    borrow_at: datetime
    due_at: datetime
    purpose: str
    status: RequestStatus
    decided_by: int | None
    decided_at: datetime | None
    decision_remarks: str | None
    canceled_at: datetime | None
    created_at: datetime
    equipment_name: str
    asset_code: str
    equipment_state: ServiceStatus
    loan: LoanOut | None
    is_overdue: bool
    was_returned_late: bool


class DashboardOut(BaseModel):
    requests_by_status: dict[RequestStatus, int]
    overdue: int


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    actor_id: int
    action: str
    entity_type: str
    entity_id: int
    details: dict
    created_at: datetime
