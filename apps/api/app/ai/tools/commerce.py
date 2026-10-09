"""Typed adapters that make commerce services callable by a future workflow."""

from app.schemas.commerce import (
    OrderLookupInput,
    OrderLookupResult,
    ProductLookupInput,
    ProductLookupResult,
    ProductSearchInput,
    ProductSearchResult,
)
from app.services.commerce_lookup import CommerceLookupService


class CommerceTools:
    """Database-free facade for graph/tool layers once a service is constructed."""

    def __init__(self, service: CommerceLookupService) -> None:
        self._service = service

    def lookup_order(self, order_number: str) -> OrderLookupResult:
        data = OrderLookupInput(order_number=order_number)
        return self._service.lookup_order(data.order_number)

    def get_product(
        self, identifier: str, *, size: str | None = None, color: str | None = None
    ) -> ProductLookupResult:
        data = ProductLookupInput(identifier=identifier, size=size, color=color)
        return self._service.get_product(data.identifier, size=data.size, color=data.color)

    def search_products(
        self, query: str, *, category: str | None = None, limit: int = 10
    ) -> ProductSearchResult:
        data = ProductSearchInput(query=query, category=category, limit=limit)
        return self._service.search_products(data.query, category=data.category, limit=data.limit)
