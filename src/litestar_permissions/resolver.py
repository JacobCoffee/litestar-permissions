from __future__ import annotations

import time
from collections import OrderedDict
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from litestar_permissions.config import PermissionsConfig


class PermissionResolver:
    """Resolves whether a user has a specific permission, optionally scoped to a resource.

    Supports hierarchical inheritance: if a user has org-admin on org X,
    they inherit all permissions on projects and applications within org X.
    """

    def __init__(self, config: PermissionsConfig, models: dict[str, type]) -> None:
        self.config = config
        self.models = models
        self._cache: OrderedDict[str, tuple[bool, float]] = OrderedDict()

    def can(
        self,
        user_id: UUID | str,
        permission: str,
        resource_type: str | None = None,
        resource_id: UUID | str | None = None,
        *,
        db: Session,
    ) -> bool:
        """Check if user has the given permission, optionally scoped to a resource."""
        cache_key = f"{user_id}:{permission}:{resource_type}:{resource_id}"

        # Check cache
        if self.config.cache_ttl > 0:
            cached = self._cache.get(cache_key)
            if cached is not None:
                result, ts = cached
                if time.monotonic() - ts < self.config.cache_ttl:
                    self._cache.move_to_end(cache_key)
                    return result
                else:
                    del self._cache[cache_key]

        result = self._resolve(user_id, permission, resource_type, resource_id, db=db)

        # Store in cache
        if self.config.cache_ttl > 0:
            self._cache[cache_key] = (result, time.monotonic())
            # LRU eviction
            while len(self._cache) > self.config.cache_max_size:
                self._cache.popitem(last=False)

        return result

    def _resolve(
        self,
        user_id: UUID | str,
        permission: str,
        resource_type: str | None,
        resource_id: UUID | str | None,
        *,
        db: Session,
    ) -> bool:
        """Core resolution logic."""
        Role = self.models["Role"]
        Permission = self.models["Permission"]
        RolePermission = self.models["RolePermission"]
        UserRoleAssignment = self.models["UserRoleAssignment"]

        # Build the set of resource scopes to check (including ancestors)
        scopes: list[tuple[str | None, UUID | str | None]] = [(None, None)]  # global
        if resource_type and resource_id:
            scopes.append((resource_type, resource_id))
            # Walk up the hierarchy
            current_type = resource_type
            current_id = resource_id
            while current_type in self.config.hierarchy:
                parent_type = self.config.hierarchy[current_type]
                # Resolve parent ID via the resource_resolver callback
                if self.config.resource_resolver:
                    parent_resource = self.config.resource_resolver(current_type, current_id, db)
                    if parent_resource and parent_resource.parent:
                        current_type = parent_type
                        current_id = parent_resource.parent.id
                        scopes.append((current_type, current_id))
                    else:
                        break
                else:
                    break

        # Query: does user have ANY role at ANY of these scopes
        # that includes the requested permission?
        stmt = (
            select(Permission.codename)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRoleAssignment, UserRoleAssignment.role_id == Role.id)
            .where(UserRoleAssignment.user_id == user_id)
            .where(Permission.codename == permission)
        )

        # Filter by scopes
        scope_filters = []
        for scope_type, scope_id in scopes:
            if scope_type is None:
                scope_filters.append(
                    and_(
                        UserRoleAssignment.resource_type.is_(None),
                        UserRoleAssignment.resource_id.is_(None),
                    )
                )
            else:
                scope_filters.append(
                    and_(
                        UserRoleAssignment.resource_type == scope_type,
                        UserRoleAssignment.resource_id == scope_id,
                    )
                )

        stmt = stmt.where(or_(*scope_filters))
        result = db.execute(stmt).first()
        return result is not None

    def get_user_permissions(
        self,
        user_id: UUID | str,
        resource_type: str | None = None,
        resource_id: UUID | str | None = None,
        *,
        db: Session,
    ) -> set[str]:
        """Get all permission codenames a user has at the given scope (+ ancestors)."""
        Role = self.models["Role"]
        Permission = self.models["Permission"]
        RolePermission = self.models["RolePermission"]
        UserRoleAssignment = self.models["UserRoleAssignment"]

        scopes: list[tuple[str | None, UUID | str | None]] = [(None, None)]
        if resource_type and resource_id:
            scopes.append((resource_type, resource_id))
            current_type = resource_type
            current_id = resource_id
            while current_type in self.config.hierarchy:
                parent_type = self.config.hierarchy[current_type]
                if self.config.resource_resolver:
                    parent_resource = self.config.resource_resolver(current_type, current_id, db)
                    if parent_resource and parent_resource.parent:
                        current_type = parent_type
                        current_id = parent_resource.parent.id
                        scopes.append((current_type, current_id))
                    else:
                        break
                else:
                    break

        stmt = (
            select(Permission.codename)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRoleAssignment, UserRoleAssignment.role_id == Role.id)
            .where(UserRoleAssignment.user_id == user_id)
        )

        scope_filters = []
        for scope_type, scope_id in scopes:
            if scope_type is None:
                scope_filters.append(
                    and_(
                        UserRoleAssignment.resource_type.is_(None),
                        UserRoleAssignment.resource_id.is_(None),
                    )
                )
            else:
                scope_filters.append(
                    and_(
                        UserRoleAssignment.resource_type == scope_type,
                        UserRoleAssignment.resource_id == scope_id,
                    )
                )

        stmt = stmt.where(or_(*scope_filters))
        rows = db.execute(stmt).all()
        return {row[0] for row in rows}

    def invalidate_user(self, user_id: UUID | str) -> None:
        """Remove all cached entries for a user."""
        prefix = f"{user_id}:"
        keys_to_remove = [k for k in self._cache if k.startswith(prefix)]
        for k in keys_to_remove:
            del self._cache[k]

    def invalidate_all(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()
