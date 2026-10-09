"""Parameterized, read-only access to structured commerce data."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Order, OrderItem, Product, ProductVariant
from app.schemas.commerce import (
    CustomerSummary,
    OrderDetails,
    OrderItemResult,
    OrderLookupResult,
    ProductDetails,
    ProductLookupResult,
    ProductSearchMatch,
    ProductSearchResult,
    ShipmentResult,
    VariantResult,
)


class CommerceLookupService:
    """Application service for typed, read-only order and product lookups."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def lookup_order(self, order_number: str) -> OrderLookupResult:
        normalized = order_number.strip().upper()
        if not normalized:
            return OrderLookupResult(found=False, message="Order number is required.")
        order = self._session.scalar(
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.shipment),
                selectinload(Order.items)
                .selectinload(OrderItem.product_variant)
                .selectinload(ProductVariant.product),
            )
            .where(Order.order_number == normalized)
        )
        if order is None:
            return OrderLookupResult(found=False, message=f"Order {normalized} was not found.")
        return OrderLookupResult(found=True, order=self._order_details(order))

    def get_product(
        self, identifier: str, *, size: str | None = None, color: str | None = None
    ) -> ProductLookupResult:
        normalized = identifier.strip()
        if not normalized:
            return ProductLookupResult(found=False, message="Product identifier is required.")
        product = self._session.scalar(
            select(Product)
            .options(selectinload(Product.variants))
            .where(or_(Product.sku == normalized.upper(), Product.name.ilike(normalized)))
        )
        if product is None:
            return ProductLookupResult(found=False, message=f"Product {normalized!r} was not found.")

        variants = [self._variant_result(variant) for variant in product.variants]
        matching_variants = [
            variant
            for variant in variants
            if (size is None or (variant.size or "").casefold() == size.strip().casefold())
            and (color is None or (variant.color or "").casefold() == color.strip().casefold())
        ]
        message = None
        if (size is not None or color is not None) and not matching_variants:
            message = "No variants match the requested size and color."
        return ProductLookupResult(
            found=True,
            product=ProductDetails(
                name=product.name,
                sku=product.sku,
                description=product.description,
                category=product.category,
                active=self._active(product),
                variants=variants,
            ),
            matching_variants=matching_variants,
            message=message,
        )

    def search_products(
        self, query: str, *, category: str | None = None, limit: int = 10
    ) -> ProductSearchResult:
        normalized = query.strip()
        if not normalized:
            return ProductSearchResult(matches=[])
        pattern = f"%{normalized}%"
        statement = select(Product).where(
            or_(Product.name.ilike(pattern), Product.category.ilike(pattern), Product.sku.ilike(pattern))
        )
        if category:
            statement = statement.where(Product.category.ilike(category.strip()))
        products = self._session.scalars(statement.order_by(Product.name).limit(limit)).all()
        return ProductSearchResult(
            matches=[
                ProductSearchMatch(
                    name=product.name,
                    sku=product.sku,
                    category=product.category,
                    active=self._active(product),
                )
                for product in products
            ]
        )

    @staticmethod
    def _variant_result(variant: ProductVariant) -> VariantResult:
        return VariantResult(
            sku=variant.sku,
            size=variant.size,
            color=variant.color,
            price=variant.price,
            stock_quantity=variant.stock_quantity,
            available=variant.stock_quantity > 0,
        )

    @staticmethod
    def _active(product: Product) -> bool:
        """Apply the model's active-by-default contract before an ORM object is flushed."""
        return True if product.active is None else product.active

    def _order_details(self, order: Order) -> OrderDetails:
        return OrderDetails(
            order_number=order.order_number,
            status=order.status.value,
            created_at=order.created_at,
            total=order.total,
            customer=CustomerSummary(name=order.customer.name, email=order.customer.email),
            items=[
                OrderItemResult(
                    product_name=item.product_variant.product.name,
                    variant_sku=item.product_variant.sku,
                    size=item.product_variant.size,
                    color=item.product_variant.color,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                )
                for item in order.items
            ],
            shipment=(
                ShipmentResult(
                    status=order.shipment.status.value,
                    carrier=order.shipment.carrier,
                    tracking_number=order.shipment.tracking_number,
                    estimated_delivery=order.shipment.estimated_delivery,
                    shipped_at=order.shipment.shipped_at,
                    delivered_at=order.shipment.delivered_at,
                )
                if order.shipment
                else None
            ),
        )
