from typing import Literal

from pydantic import BaseModel

Availability = Literal["available", "reserved", "on_loan", "maintenance", "retired"]


class CategoryOut(BaseModel):
    id: int
    name: str
    description: str


class EquipmentOut(BaseModel):
    id: int
    asset_code: str
    name: str
    description: str
    location: str
    category_id: int
    category: str
    condition: str
    availability: Availability


class EquipmentPage(BaseModel):
    items: list[EquipmentOut]
    total: int
    offset: int
    limit: int


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


def errors(*codes: int):
    return {code: {"model": ErrorResponse} for code in codes}
