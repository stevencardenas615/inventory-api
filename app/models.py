from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from decimal import Decimal

class Status(str, Enum):
    AVAILABLE = "available"
    NOT_AVAILABLE = "not_available"
    DELETED = "deleted"
    SOLD = "sold"

class EditableStatus(str, Enum):
    AVAILABLE = "available"
    NOT_AVAILABLE = "not_available"
    DELETED = "deleted"

class ProductCreate(BaseModel):
    manifest_id: int
    barcode: str
    product_name: str
    retail_price: Decimal
    list_price: Decimal
    status: Status = Status.NOT_AVAILABLE

class Product(ProductCreate):
    product_id: int
    sold_price: Decimal | None = None
    sold_at: datetime | None = None

class ProductUpdate(BaseModel):
    product_name: str | None = None
    retail_price: Decimal | None = None
    list_price: Decimal | None = None
    status: EditableStatus | None = None

class ManifestCreate(BaseModel):
    purchase_date: datetime
    cost: Decimal

class Manifest(ManifestCreate):
    manifest_id: int
    entered_by: int

class ManifestUpdate(BaseModel):
    purchase_date: datetime | None = None
    cost: Decimal | None = None

class UserBase(BaseModel):
    username: str
    first_name: str
    last_name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    user_id: int
    created_at: datetime

class UserInDB(User):
    password_hash: str

class UserUpdate(BaseModel):
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None    
