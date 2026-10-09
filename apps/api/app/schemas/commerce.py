"""Typed contracts for read-only commerce lookup operations."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OrderLookupInput(BaseModel):
    order_number: str = Field(min_length=1, max_length=100)


class ProductLookupInput(BaseModel):
    identifier: str = Field(min_length=1, max_length=255)
    size: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=50)


class ProductSearchInput(BaseModel):
    query: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    limit: int = Field(default=10, ge=1, le=25)


class CustomerSummary(BaseModel):
    name: str
    email: str


class VariantResult(BaseModel):
    sku: str
    size: str | None
    color: str | None
    price: Decimal
    stock_quantity: int
    available: bool


class OrderItemResult(BaseModel):
    product_name: str
    variant_sku: str
    size: str | None
    color: str | None
    quantity: int
    unit_price: Decimal


class ShipmentResult(BaseModel):
    status: str
    carrier: str | None
    tracking_number: str | None
    estimated_delivery: date | None
    shipped_at: datetime | None
    delivered_at: datetime | None


class OrderDetails(BaseModel):
    order_number: str
    status: str
    created_at: datetime
    total: Decimal
    customer: CustomerSummary
    items: list[OrderItemResult]
    shipment: ShipmentResult | None


class OrderLookupResult(BaseModel):
    found: bool
    order: OrderDetails | None = None
    message: str | None = None


class ProductDetails(BaseModel):
    name: str
    sku: str
    description: str
    category: str
    active: bool
    variants: list[VariantResult]


class ProductLookupResult(BaseModel):
    found: bool
    product: ProductDetails | None = None
    matching_variants: list[VariantResult] = Field(default_factory=list)
    message: str | None = None


class ProductSearchMatch(BaseModel):
    name: str
    sku: str
    category: str
    active: bool


class ProductSearchResult(BaseModel):
    matches: list[ProductSearchMatch]
