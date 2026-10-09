"""Deterministic fictional commerce data for local demonstrations.

Run after applying migrations:

    python -m app.db.seed --reset
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid5

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import (
    Customer,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    ProductVariant,
    Shipment,
    ShipmentStatus,
)

_NAMESPACE = UUID("bb31dc9a-1c9b-4e40-9489-2e1e957fe8ba")
_CREATED_AT = datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)


@dataclass(frozen=True)
class SeedRecords:
    customers: list[Customer]
    products: list[Product]
    orders: list[Order]


class SeedDataExistsError(RuntimeError):
    """Raised when preserving existing commerce data would make a seed ambiguous."""


def _id(key: str) -> UUID:
    return uuid5(_NAMESPACE, key)


def _money(value: str) -> Decimal:
    return Decimal(value)


def build_seed_records() -> SeedRecords:
    """Build a fresh, deterministic object graph without writing to a database."""
    customers = [
        Customer(id=_id("customer:maya-chen"), name="Maya Chen", email="maya.chen@example.test", created_at=_CREATED_AT, updated_at=_CREATED_AT),
        Customer(id=_id("customer:eli-turner"), name="Eli Turner", email="eli.turner@example.test", created_at=_CREATED_AT, updated_at=_CREATED_AT),
        Customer(id=_id("customer:nora-patel"), name="Nora Patel", email="nora.patel@example.test", created_at=_CREATED_AT, updated_at=_CREATED_AT),
        Customer(id=_id("customer:jonah-reed"), name="Jonah Reed", email="jonah.reed@example.test", created_at=_CREATED_AT, updated_at=_CREATED_AT),
        Customer(id=_id("customer:lena-morris"), name="Lena Morris", email="lena.morris@example.test", created_at=_CREATED_AT, updated_at=_CREATED_AT),
        Customer(id=_id("customer:devon-brooks"), name="Devon Brooks", email="devon.brooks@example.test", created_at=_CREATED_AT, updated_at=_CREATED_AT),
    ]
    customer_by_email = {customer.email: customer for customer in customers}

    products: list[Product] = []
    variants: dict[str, ProductVariant] = {}

    def product(sku: str, name: str, category: str, description: str, variant_data: list[tuple[str, str | None, str | None, str, int]]) -> None:
        item = Product(id=_id(f"product:{sku}"), sku=sku, name=name, category=category, description=description, created_at=_CREATED_AT, updated_at=_CREATED_AT)
        for variant_sku, size, color, price, stock in variant_data:
            variant = ProductVariant(id=_id(f"variant:{variant_sku}"), product_id=item.id, sku=variant_sku, size=size, color=color, price=_money(price), stock_quantity=stock, created_at=_CREATED_AT, updated_at=_CREATED_AT)
            item.variants.append(variant)
            variants[variant_sku] = variant
        products.append(item)

    product("SH-TRAIL-RUNNER", "Trail Runner Shoes", "Footwear", "Responsive trail shoes with a grippy all-terrain outsole and breathable mesh upper.", [
        ("SH-TRAIL-RUNNER-PINE-8", "8", "Pine", "129.00", 7), ("SH-TRAIL-RUNNER-PINE-9", "9", "Pine", "129.00", 12),
        ("SH-TRAIL-RUNNER-PINE-10", "10", "Pine", "129.00", 9), ("SH-TRAIL-RUNNER-PINE-11", "11", "Pine", "129.00", 3),
        ("SH-TRAIL-RUNNER-SLATE-9", "9", "Slate", "129.00", 6), ("SH-TRAIL-RUNNER-SLATE-10", "10", "Slate", "129.00", 0),
    ])
    product("SH-HORIZON-HIKER", "Horizon Hiker Boots", "Footwear", "Water-resistant day-hiking boots with supportive midsoles.", [
        ("SH-HORIZON-HIKER-8-UMBER", "8", "Umber", "164.00", 5), ("SH-HORIZON-HIKER-9-UMBER", "9", "Umber", "164.00", 4),
        ("SH-HORIZON-HIKER-10-UMBER", "10", "Umber", "164.00", 2), ("SH-HORIZON-HIKER-11-UMBER", "11", "Umber", "164.00", 0),
    ])
    product("SH-CLOUDSTREET", "Cloudstreet Sneakers", "Footwear", "Light everyday sneakers with cushioned foam support.", [
        ("SH-CLOUDSTREET-8-SAND", "8", "Sand", "98.00", 14), ("SH-CLOUDSTREET-9-SAND", "9", "Sand", "98.00", 10), ("SH-CLOUDSTREET-10-NAVY", "10", "Navy", "98.00", 8),
    ])
    product("AP-MERINO-TEE", "Merino Base Tee", "Apparel", "Soft merino blend base layer designed for everyday movement.", [
        ("AP-MERINO-TEE-S-ASH", "S", "Ash", "58.00", 11), ("AP-MERINO-TEE-M-ASH", "M", "Ash", "58.00", 15), ("AP-MERINO-TEE-L-FOREST", "L", "Forest", "58.00", 6),
    ])
    product("AP-RIDGE-FLEECE", "Ridge Fleece Pullover", "Apparel", "Midweight grid fleece with a half zip and stand collar.", [
        ("AP-RIDGE-FLEECE-S-OAT", "S", "Oat", "92.00", 5), ("AP-RIDGE-FLEECE-M-OAT", "M", "Oat", "92.00", 8), ("AP-RIDGE-FLEECE-L-NAVY", "L", "Navy", "92.00", 4),
    ])
    product("AP-TRAVERSE-SHORT", "Traverse Trail Shorts", "Apparel", "Quick-dry five-inch trail shorts with a secure rear pocket.", [
        ("AP-TRAVERSE-SHORT-S", "S", None, "64.00", 10), ("AP-TRAVERSE-SHORT-M", "M", None, "64.00", 7), ("AP-TRAVERSE-SHORT-L", "L", None, "64.00", 1),
    ])
    product("AP-ALPINE-SHELL", "Alpine Rain Shell", "Apparel", "Packable waterproof shell for sudden mountain weather.", [
        ("AP-ALPINE-SHELL-S-CITRON", "S", "Citron", "189.00", 3), ("AP-ALPINE-SHELL-M-CITRON", "M", "Citron", "189.00", 5), ("AP-ALPINE-SHELL-L-NAVY", "L", "Navy", "189.00", 2),
    ])
    product("AP-TRAIL-SOCK", "Trail Crew Socks", "Apparel", "Cushioned merino-blend crew socks for long days on foot.", [
        ("AP-TRAIL-SOCK-SM", "S/M", None, "18.00", 24), ("AP-TRAIL-SOCK-LXL", "L/XL", None, "18.00", 19),
    ])
    product("AC-CAMP-MUG", "Campfire Enamel Mug", "Accessories", "Twelve-ounce enamel mug for coffee at camp or at your desk.", [
        ("AC-CAMP-MUG-CREAM", None, "Cream", "22.00", 20), ("AC-CAMP-MUG-SAGE", None, "Sage", "22.00", 9), ("AC-CAMP-MUG-RUST", None, "Rust", "22.00", 0),
    ])
    product("AC-SUMMIT-CAP", "Summit Five-Panel Cap", "Accessories", "Lightweight quick-dry cap with an adjustable webbing strap.", [
        ("AC-SUMMIT-CAP-PINE", None, "Pine", "34.00", 12), ("AC-SUMMIT-CAP-CLAY", None, "Clay", "34.00", 2),
    ])
    product("TR-WAYPOINT-PACK", "Waypoint Daypack 22L", "Travel & Outdoor", "Versatile 22-liter daypack with a hydration sleeve and laptop pocket.", [
        ("TR-WAYPOINT-PACK-BLACK", None, "Black", "118.00", 8), ("TR-WAYPOINT-PACK-MOSS", None, "Moss", "118.00", 5),
    ])
    product("TR-PACKING-CUBES", "Waypoint Packing Cubes", "Travel & Outdoor", "Three-piece ripstop packing cube set for organized travel.", [
        ("TR-PACKING-CUBES-SLATE", None, "Slate", "36.00", 16), ("TR-PACKING-CUBES-SAND", None, "Sand", "36.00", 6),
    ])
    product("TR-FIELD-NOTES", "Backcountry Field Notes", "Travel & Outdoor", "Weather-resistant pocket notebook with dot-grid pages.", [
        ("TR-FIELD-NOTES-STD", None, None, "14.00", 30),
    ])

    orders: list[Order] = []

    def order(number: str, email: str, status: OrderStatus, item_data: list[tuple[str, int, str]], shipment_data: tuple[str, str, ShipmentStatus, date | None, datetime | None, datetime | None] | None = None) -> None:
        customer = customer_by_email[email]
        items = [OrderItem(id=_id(f"item:{number}:{sku}"), product_variant_id=variants[sku].id, product_variant=variants[sku], quantity=quantity, unit_price=_money(price)) for sku, quantity, price in item_data]
        total = sum((item.unit_price * item.quantity for item in items), Decimal("0.00"))
        placed = _CREATED_AT.replace(day=16 + len(orders))
        record = Order(id=_id(f"order:{number}"), order_number=number, customer_id=customer.id, customer=customer, status=status, total=total, created_at=placed, updated_at=placed, items=items)
        if shipment_data:
            carrier, tracking, shipment_status, eta, shipped_at, delivered_at = shipment_data
            record.shipment = Shipment(id=_id(f"shipment:{number}"), order_id=record.id, carrier=carrier, tracking_number=tracking, status=shipment_status, estimated_delivery=eta, shipped_at=shipped_at, delivered_at=delivered_at, created_at=placed, updated_at=placed)
        orders.append(record)

    shipped_at = datetime(2026, 2, 2, 14, 0, tzinfo=timezone.utc)
    delivered_at = datetime(2026, 2, 6, 16, 30, tzinfo=timezone.utc)
    order("ORD-1001", "maya.chen@example.test", OrderStatus.DELIVERED, [("AC-CAMP-MUG-CREAM", 1, "22.00"), ("TR-FIELD-NOTES-STD", 1, "14.00")], ("SwiftShip", "SS-7814-1001-QM", ShipmentStatus.DELIVERED, date(2026, 1, 21), datetime(2026, 1, 18, 12, tzinfo=timezone.utc), datetime(2026, 1, 21, 15, tzinfo=timezone.utc)))
    order("ORD-1002", "eli.turner@example.test", OrderStatus.SHIPPED, [("AP-RIDGE-FLEECE-M-OAT", 1, "92.00")], ("RapidPost", "RP-3902-1002-LK", ShipmentStatus.IN_TRANSIT, date(2026, 2, 4), datetime(2026, 2, 1, 9, tzinfo=timezone.utc), None))
    order("ORD-1003", "nora.patel@example.test", OrderStatus.PROCESSING, [("TR-WAYPOINT-PACK-MOSS", 1, "118.00"), ("TR-PACKING-CUBES-SLATE", 1, "36.00")])
    order("ORD-1004", "jonah.reed@example.test", OrderStatus.PAID, [("SH-CLOUDSTREET-10-NAVY", 1, "98.00")])
    order("ORD-1005", "lena.morris@example.test", OrderStatus.DELIVERED, [("SH-HORIZON-HIKER-9-UMBER", 1, "164.00")], ("ParcelNorth", "PN-1880-1005-DR", ShipmentStatus.DELIVERED, date(2026, 2, 6), shipped_at, delivered_at))
    order("ORD-1006", "devon.brooks@example.test", OrderStatus.CANCELLED, [("AP-ALPINE-SHELL-M-CITRON", 1, "189.00")])
    order("ORD-1007", "maya.chen@example.test", OrderStatus.SHIPPED, [("SH-TRAIL-RUNNER-PINE-10", 1, "129.00"), ("AP-TRAIL-SOCK-LXL", 2, "18.00")], ("ParcelNorth", "PN-2048-1007-AX", ShipmentStatus.IN_TRANSIT, date(2026, 2, 12), datetime(2026, 2, 8, 11, tzinfo=timezone.utc), None))
    order("ORD-1008", "eli.turner@example.test", OrderStatus.DELIVERED, [("TR-WAYPOINT-PACK-BLACK", 1, "118.00"), ("AC-SUMMIT-CAP-PINE", 1, "34.00")], ("SwiftShip", "SS-8142-1008-CN", ShipmentStatus.DELIVERED, date(2026, 2, 10), datetime(2026, 2, 7, 10, tzinfo=timezone.utc), datetime(2026, 2, 10, 13, tzinfo=timezone.utc)))
    order("ORD-1009", "nora.patel@example.test", OrderStatus.SHIPPED, [("AP-MERINO-TEE-L-FOREST", 2, "58.00")], ("RapidPost", "RP-4188-1009-TJ", ShipmentStatus.OUT_FOR_DELIVERY, date(2026, 2, 13), datetime(2026, 2, 10, 8, tzinfo=timezone.utc), None))
    order("ORD-1010", "jonah.reed@example.test", OrderStatus.PAID, [("AC-CAMP-MUG-SAGE", 2, "22.00"), ("TR-FIELD-NOTES-STD", 1, "14.00")])
    order("ORD-1011", "lena.morris@example.test", OrderStatus.PROCESSING, [("AP-TRAVERSE-SHORT-L", 1, "64.00"), ("AC-SUMMIT-CAP-CLAY", 1, "34.00")])
    order("ORD-1012", "devon.brooks@example.test", OrderStatus.CANCELLED, [("SH-TRAIL-RUNNER-SLATE-9", 1, "129.00")])
    order("ORD-1013", "maya.chen@example.test", OrderStatus.DELIVERED, [("TR-PACKING-CUBES-SAND", 1, "36.00"), ("AP-TRAIL-SOCK-SM", 3, "18.00")], ("ParcelNorth", "PN-2256-1013-BV", ShipmentStatus.DELIVERED, date(2026, 2, 15), datetime(2026, 2, 12, 10, tzinfo=timezone.utc), datetime(2026, 2, 15, 14, tzinfo=timezone.utc)))
    order("ORD-1014", "eli.turner@example.test", OrderStatus.SHIPPED, [("AP-ALPINE-SHELL-S-CITRON", 1, "189.00")], ("SwiftShip", "SS-8430-1014-GH", ShipmentStatus.SHIPPED, date(2026, 2, 18), datetime(2026, 2, 15, 9, tzinfo=timezone.utc), None))
    return SeedRecords(customers=customers, products=products, orders=orders)


def seed_database(session: Session, *, reset: bool = False) -> SeedRecords:
    """Insert the dataset, refusing to overwrite existing commerce data by default."""
    has_existing_data = any(
        session.scalar(select(model.id).limit(1)) is not None
        for model in (Customer, Product, ProductVariant, Order, OrderItem, Shipment)
    )
    if has_existing_data and not reset:
        raise SeedDataExistsError("Commerce data already exists. Re-run with --reset to replace local commerce data.")
    if reset:
        for model in (OrderItem, Shipment, Order, ProductVariant, Product, Customer):
            session.execute(delete(model))
    records = build_seed_records()
    session.add_all([*records.customers, *records.products, *records.orders])
    session.commit()
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed deterministic fictional commerce demo data.")
    parser.add_argument("--reset", action="store_true", help="replace all local commerce records before seeding")
    args = parser.parse_args()
    with SessionLocal() as session:
        records = seed_database(session, reset=args.reset)
    print(f"Seeded {len(records.customers)} customers, {len(records.products)} products, and {len(records.orders)} orders.")


if __name__ == "__main__":
    main()
