from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from sqlalchemy import and_, or_, select

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from litestar.handlers import BaseRouteHandler


def _is_superuser(user: object) -> bool:
    return getattr(user, "is_superuser", False) or getattr(user, "admin", False)


def require_permission(
    *permissions: str,
    resource_type_param: str | None = None,
    resource_id_param: str | None = None,
) -> Any:
    """Guard factory that checks if the current user has ALL of the specified permissions.

    Args:
        permissions: Permission codenames the user must have (e.g. "application:deploy").
        resource_type_param: Path/query param name that holds the resource type.
            If None, uses resource_id_param with a fixed resource_type from the guard config.
        resource_id_param: Path/query param name that holds the resource ID.

    Usage:
        @get("/apps/{app_id}/deploy", guards=[require_permission("application:deploy", resource_id_param="app_id")])

    Note:
        Consumers must populate ``connection.scope["db_session"]`` with a per-request
        ``AsyncSession`` (e.g. via middleware or a dependency that writes to scope).
    """

    async def guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
        permissions_config = connection.app.state.get("permissions_config")
        user_key = permissions_config.user_key if permissions_config else "user"
        user = connection.scope.get(user_key)
        if user is None:
            raise NotAuthorizedException("Authentication required")

        if permissions_config and permissions_config.superuser_bypass and _is_superuser(user):
            return

        resolver = connection.app.state.get("permissions_resolver")
        if resolver is None:
            raise PermissionDeniedException("Permissions system not configured")

        db = connection.scope.get("db_session")
        if db is None:
            raise PermissionDeniedException("db_session not found in request scope")

        resource_type, resource_id = _resolve_resource_scope(
            connection, permissions, resource_type_param, resource_id_param, permissions_config
        )

        for perm in permissions:
            if not await resolver.can(user.id, perm, resource_type, resource_id, db=db):
                raise PermissionDeniedException(f"Missing permission: {perm}")

    return guard


def _resolve_resource_scope(
    connection: ASGIConnection,
    permissions: tuple[str, ...],
    resource_type_param: str | None,
    resource_id_param: str | None,
    permissions_config: object | None,
) -> tuple[str | None, str | None]:
    """Extract resource type and ID from path params."""
    resource_type = None
    resource_id = None
    if resource_id_param:
        resource_id = connection.path_params.get(resource_id_param)
        if resource_type_param:
            resource_type = connection.path_params.get(resource_type_param)
        elif resource_id and permissions_config:
            for perm in permissions:
                if ":" in perm:
                    resource_type = perm.split(":")[0]
                    break
    return resource_type, resource_id


def require_role(
    *role_names: str,
    resource_type_param: str | None = None,
    resource_id_param: str | None = None,
) -> Any:
    """Guard factory that checks if the current user has ANY of the specified roles.

    Args:
        role_names: Role names (user must have at least one).
        resource_type_param: Path param for resource type.
        resource_id_param: Path param for resource ID.

    Note:
        Consumers must populate ``connection.scope["db_session"]`` with a per-request
        ``AsyncSession`` (e.g. via middleware or a dependency that writes to scope).
    """

    async def guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
        permissions_config = connection.app.state.get("permissions_config")
        user_key = permissions_config.user_key if permissions_config else "user"
        user = connection.scope.get(user_key)
        if user is None:
            raise NotAuthorizedException("Authentication required")

        if permissions_config and permissions_config.superuser_bypass and _is_superuser(user):
            return

        db = connection.scope.get("db_session")
        if db is None:
            raise PermissionDeniedException("db_session not found in request scope")

        models = connection.app.state.get("permissions_models")
        if not models:
            raise PermissionDeniedException("Permissions system not configured")

        user_role_assignment = models["UserRoleAssignment"]
        role_model = models["Role"]

        resource_type = None
        resource_id = None
        if resource_id_param:
            resource_id = connection.path_params.get(resource_id_param)
            if resource_type_param:
                resource_type = connection.path_params.get(resource_type_param)

        stmt = (
            select(role_model.name)
            .join(user_role_assignment, user_role_assignment.role_id == role_model.id)
            .where(user_role_assignment.user_id == user.id)
            .where(role_model.name.in_(role_names))
        )

        scope_filters = [
            and_(
                user_role_assignment.resource_type.is_(None),
                user_role_assignment.resource_id.is_(None),
            )
        ]
        if resource_type and resource_id:
            scope_filters.append(
                and_(
                    user_role_assignment.resource_type == resource_type,
                    user_role_assignment.resource_id == resource_id,
                )
            )

        stmt = stmt.where(or_(*scope_filters))
        result = await db.execute(stmt)
        if result.first() is None:
            raise PermissionDeniedException(f"Required role: {' or '.join(role_names)}")

    return guard
