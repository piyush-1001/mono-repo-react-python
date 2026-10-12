"""Shared enums and type aliases."""

from enum import StrEnum


class RoleType(StrEnum):
    """Roles a user can hold in the platform."""

    ADMIN = "ADMIN"
    STAFF = "STAFF"
    USER = "USER"
    ANY = "ANY"
    OPTIONAL = "OPTIONAL"


class TokenType(StrEnum):
    """JWT token flavours issued by the service."""

    ACCESS = "access"
    REFRESH = "refresh"
    ADMIN_ACCESS = "admin_access"
    ADMIN_REFRESH = "admin_refresh"


class ProductStatusType(StrEnum):
    """Lifecycle of a product record."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class StockMovementType(StrEnum):
    """Reason a stock balance changed."""

    IN = "IN"
    OUT = "OUT"
    ADJUST = "ADJUST"


class MeasurementUnitType(StrEnum):
    """Units a product can be measured in."""

    PIECE = "PCS"
    KILOGRAM = "KG"
    GRAM = "G"
    LITRE = "L"
    METRE = "M"
    BOX = "BOX"
