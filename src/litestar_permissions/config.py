from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class PermissionsConfig:
    """Configuration for the permissions plugin."""

    # SQLAlchemy table prefix for RBAC tables (default: no prefix)
    table_prefix: str = ""

    # Cache TTL for resolved permissions (seconds). 0 = no cache.
    cache_ttl: int = 300

    # Maximum cache entries before LRU eviction
    cache_max_size: int = 10000

    # Hierarchy map: resource_type -> parent_resource_type
    # e.g. {"application": "project", "project": "organization"}
    hierarchy: dict[str, str] = field(default_factory=dict)

    # Custom function to resolve a resource from request path params.
    # Signature: (resource_type: str, resource_id: str, db_session) -> ResourceProtocol | None
    resource_resolver: Callable[..., Any] | None = None

    # User attribute on the request scope to read the current user from
    user_key: str = "user"

    # Whether superuser bypasses all permission checks
    superuser_bypass: bool = True
