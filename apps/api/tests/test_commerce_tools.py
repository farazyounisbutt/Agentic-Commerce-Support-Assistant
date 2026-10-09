from decimal import Decimal

from app.ai.tools.commerce import CommerceTools
from app.db.seed import build_seed_records
from app.services.commerce_lookup import CommerceLookupService


class _ScalarResult:
    def __init__(self, values: list[object]) -> None:
        self._values = values

    def all(self) -> list[object]:
        return self._values


class _SeedSession:
    def __init__(self) -> None:
        records = build_seed_records()
        self.orders = {order.order_number: order for order in records.orders}
        self.products = records.products

    def scalar(self, statement: object) -> object | None:
        statement_text = str(statement)
        values = set(statement.compile().params.values())
        if "orders" in statement_text:
            return next((order for number, order in self.orders.items() if number in values), None)
        return next(
            (
                product
                for product in self.products
                if product.sku in values or product.name in values
            ),
            None,
        )

    def scalars(self, statement: object) -> _ScalarResult:
        return _ScalarResult([product for product in self.products if "Trail" in product.name])


def test_order_tool_returns_ord_1007_with_shipment_and_historical_prices() -> None:
    tools = CommerceTools(CommerceLookupService(_SeedSession()))

    result = tools.lookup_order("ORD-1007")

    assert result.found is True
    assert result.order is not None
    assert result.order.status == "SHIPPED"
    assert result.order.shipment is not None
    assert result.order.shipment.carrier == "ParcelNorth"
    assert result.order.shipment.tracking_number == "PN-2048-1007-AX"
    assert result.order.items[0].variant_sku == "SH-TRAIL-RUNNER-PINE-10"
    assert result.order.items[0].unit_price == Decimal("129.00")


def test_order_tool_handles_processing_and_unknown_orders() -> None:
    service = CommerceLookupService(_SeedSession())

    processing = service.lookup_order("ORD-1003")
    unknown = service.lookup_order("ORD-9999")

    assert processing.found is True
    assert processing.order is not None
    assert processing.order.shipment is None
    assert unknown.found is False
    assert unknown.message == "Order ORD-9999 was not found."


def test_product_tool_returns_stock_and_variant_filters() -> None:
    tools = CommerceTools(CommerceLookupService(_SeedSession()))

    result = tools.get_product("SH-TRAIL-RUNNER", size="10", color="Pine")

    assert result.found is True
    assert result.product is not None
    assert result.product.name == "Trail Runner Shoes"
    assert result.matching_variants[0].stock_quantity == 9
    assert result.matching_variants[0].available is True

    unavailable = tools.get_product("SH-TRAIL-RUNNER", size="10", color="Slate")
    assert unavailable.matching_variants[0].available is False

    unknown = tools.get_product("UNKNOWN-PRODUCT")
    assert unknown.found is False
    assert unknown.message == "Product 'UNKNOWN-PRODUCT' was not found."


def test_product_search_returns_concise_matches() -> None:
    tools = CommerceTools(CommerceLookupService(_SeedSession()))

    result = tools.search_products("trail")

    assert result.matches
    assert any(match.sku == "SH-TRAIL-RUNNER" for match in result.matches)
