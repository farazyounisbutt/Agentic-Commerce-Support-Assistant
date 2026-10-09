from sqlalchemy import DateTime, Numeric

from app.db.base import Base
from app.models.commerce import OrderStatus, ShipmentStatus


def test_commerce_models_import_from_the_models_package() -> None:
    from app.models import Customer, Order, OrderItem, Product, ProductVariant, Shipment

    assert all((Customer, Product, ProductVariant, Order, OrderItem, Shipment))


def test_commerce_models_are_registered_with_expected_tables() -> None:
    assert {
        "customers",
        "products",
        "product_variants",
        "orders",
        "order_items",
        "shipments",
    }.issubset(Base.metadata.tables)


def test_order_and_shipment_statuses_are_explicit() -> None:
    assert [status.value for status in OrderStatus] == [
        "PROCESSING",
        "PAID",
        "SHIPPED",
        "DELIVERED",
        "CANCELLED",
    ]
    assert [status.value for status in ShipmentStatus] == [
        "PENDING",
        "SHIPPED",
        "IN_TRANSIT",
        "OUT_FOR_DELIVERY",
        "DELIVERED",
        "EXCEPTION",
    ]


def test_required_unique_and_nullable_columns_are_configured() -> None:
    customers = Base.metadata.tables["customers"]
    products = Base.metadata.tables["products"]
    variants = Base.metadata.tables["product_variants"]
    orders = Base.metadata.tables["orders"]
    shipments = Base.metadata.tables["shipments"]

    assert customers.c.email.unique and customers.c.email.index
    assert products.c.sku.unique and products.c.sku.index
    assert variants.c.sku.unique and variants.c.sku.index
    assert orders.c.order_number.unique and orders.c.order_number.index
    assert variants.c.size.nullable
    assert variants.c.color.nullable
    assert shipments.c.carrier.nullable
    assert shipments.c.tracking_number.nullable
    assert shipments.c.estimated_delivery.nullable


def test_monetary_columns_use_fixed_precision_numeric_types() -> None:
    tables_and_columns = [
        ("product_variants", "price"),
        ("orders", "total"),
        ("order_items", "unit_price"),
    ]

    for table_name, column_name in tables_and_columns:
        column_type = Base.metadata.tables[table_name].c[column_name].type
        assert isinstance(column_type, Numeric)
        assert (column_type.precision, column_type.scale) == (12, 2)



def test_timestamp_columns_are_timezone_aware() -> None:
    timestamp_columns = [
        ("customers", "created_at"),
        ("customers", "updated_at"),
        ("products", "created_at"),
        ("products", "updated_at"),
        ("product_variants", "created_at"),
        ("product_variants", "updated_at"),
        ("orders", "created_at"),
        ("orders", "updated_at"),
        ("shipments", "shipped_at"),
        ("shipments", "delivered_at"),
        ("shipments", "created_at"),
        ("shipments", "updated_at"),
    ]

    for table_name, column_name in timestamp_columns:
        column_type = Base.metadata.tables[table_name].c[column_name].type
        assert isinstance(column_type, DateTime)
        assert column_type.timezone is True


def test_key_relationships_and_enum_columns_are_configured() -> None:
    from app.models.commerce import Customer, Order, Product, ProductVariant, Shipment

    orders = Base.metadata.tables["orders"]
    shipments = Base.metadata.tables["shipments"]

    assert Customer.orders.property.back_populates == "customer"
    assert Product.variants.property.back_populates == "product"
    assert Order.items.property.back_populates == "order"
    assert ProductVariant.order_items.property.back_populates == "product_variant"
    assert Order.shipment.property.uselist is False
    assert Shipment.order.property.back_populates == "shipment"
    assert orders.c.status.type.enums == [status.value for status in OrderStatus]
    assert shipments.c.status.type.enums == [status.value for status in ShipmentStatus]
    assert shipments.c.order_id.unique
    assert next(iter(orders.c.customer_id.foreign_keys)).ondelete == "RESTRICT"
    assert next(iter(shipments.c.order_id.foreign_keys)).ondelete == "CASCADE"
