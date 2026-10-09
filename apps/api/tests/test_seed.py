from decimal import Decimal

from app.db.seed import build_seed_records
from app.models import OrderStatus, ShipmentStatus


def test_seed_dataset_has_expected_demo_coverage() -> None:
    records = build_seed_records()

    assert len(records.customers) == 6
    assert len(records.products) == 13
    assert len(records.orders) == 14
    assert {order.status for order in records.orders} == set(OrderStatus)

    trail_runner = next(product for product in records.products if product.sku == "SH-TRAIL-RUNNER")
    trail_variants = {variant.sku: variant for variant in trail_runner.variants}
    assert trail_variants["SH-TRAIL-RUNNER-PINE-10"].stock_quantity > 0
    assert any(variant.stock_quantity == 0 for variant in trail_variants.values())
    assert {variant.size for variant in trail_variants.values()} >= {"8", "9", "10", "11"}
    assert {variant.color for variant in trail_variants.values()} >= {"Pine", "Slate"}


def test_seed_dataset_contains_canonical_order_and_coherent_shipments() -> None:
    records = build_seed_records()
    orders = {order.order_number: order for order in records.orders}

    shipped = orders["ORD-1007"]
    assert shipped.status is OrderStatus.SHIPPED
    assert shipped.shipment is not None
    assert shipped.shipment.carrier == "ParcelNorth"
    assert shipped.shipment.tracking_number == "PN-2048-1007-AX"
    assert shipped.shipment.estimated_delivery is not None

    assert orders["ORD-1003"].status is OrderStatus.PROCESSING
    assert orders["ORD-1003"].shipment is None
    assert orders["ORD-1010"].status is OrderStatus.PAID
    assert orders["ORD-1010"].shipment is None
    assert orders["ORD-1005"].status is OrderStatus.DELIVERED
    assert orders["ORD-1005"].shipment.status is ShipmentStatus.DELIVERED
    assert orders["ORD-1012"].status is OrderStatus.CANCELLED


def test_seed_orders_preserve_prices_and_match_totals() -> None:
    records = build_seed_records()

    for order in records.orders:
        assert order.total == sum((item.unit_price * item.quantity for item in order.items), Decimal("0.00"))
        assert all(item.unit_price >= Decimal("0.00") for item in order.items)
        assert all(item.product_variant is not None for item in order.items)


def test_seed_dataset_is_deterministic_and_has_variant_types() -> None:
    first = build_seed_records()
    second = build_seed_records()

    assert [customer.id for customer in first.customers] == [customer.id for customer in second.customers]
    assert [product.sku for product in first.products] == [product.sku for product in second.products]
    assert [order.id for order in first.orders] == [order.id for order in second.orders]

    products = {product.sku: product for product in first.products}
    assert all(variant.size is None for variant in products["AC-CAMP-MUG"].variants)
    assert all(variant.color is not None for variant in products["AC-CAMP-MUG"].variants)
    assert any(
        variant.size is not None and variant.color is not None
        for variant in products["SH-TRAIL-RUNNER"].variants
    )
