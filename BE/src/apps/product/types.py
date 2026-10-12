"""Product feature types."""

from enum import StrEnum


class ProductSortField(StrEnum):
    """Fields that can be used for sorting product lists."""

    NAME = "name"
    SKU = "sku"
    PRICE = "price"
    STOCK = "stock"
    CREATED_AT = "createdAt"
