from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field

# What the columns in schema.sql can hold. Checking here turns bad input into a 422
# with a reason, instead of a database error that reaches the client as a 500.
Money = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]   # NUMERIC(10, 2), never negative
RowId = Annotated[int, Field(ge=1, le=2_147_483_647)]                      # a Postgres int primary key
ShortText = Annotated[str, Field(min_length=1, max_length=200)]            # a name or barcode, not empty

class Status(str, Enum):
    AVAILABLE = "available"
    NOT_AVAILABLE = "not_available"
    DELETED = "deleted"
    SOLD = "sold"

class EditableStatus(str, Enum):
    # What a client may set on create and PATCH. 'sold' is set only by the sell
    # route and 'deleted' only by DELETE, so each has exactly one way in.
    AVAILABLE = "available"
    NOT_AVAILABLE = "not_available"

class ProductBase(BaseModel):
    manifest_id: RowId
    barcode: ShortText
    product_name: ShortText
    retail_price: Money
    list_price: Money

class ProductCreate(ProductBase):
    status: EditableStatus = EditableStatus.NOT_AVAILABLE

class Product(ProductBase):
    product_id: int
    status: Status
    sold_price: Decimal | None = None
    sold_at: datetime | None = None

class ProductUpdate(BaseModel):
    product_name: ShortText | None = None
    retail_price: Money | None = None
    list_price: Money | None = None
    status: EditableStatus | None = None

class ManifestCreate(BaseModel):
    purchase_date: date
    cost: Money

class Manifest(ManifestCreate):
    manifest_id: int
    entered_by: int

class ManifestSummary(BaseModel):
    manifest_id: int
    cost: Decimal
    items: int              # products on the manifest, deleted ones left out
    sold: int
    available: int
    not_available: int
    revenue: Decimal        # what the sold products brought in
    profit: Decimal         # revenue minus the manifest's cost, so far

class UserBase(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=50)]
    first_name: ShortText
    last_name: ShortText

class UserCreate(UserBase):
    password: Annotated[str, Field(min_length=8, max_length=128)]

class User(UserBase):
    user_id: int
    created_at: datetime

class ProductSell(BaseModel):
    sold_price: Money
