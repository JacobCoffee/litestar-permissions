from typing import TYPE_CHECKING, Any

from litestar.exceptions import NotAuthorizedException, PermissionDeniedException

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from litestar.handlers import BaseRouteHandler


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
    """

    async def guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
        user = connection.scope.get("user")
        if user is None:
            raise NotAuthorizedException("Authentication required")

        # Superuser bypass
        permissions_config = connection.app.state.get("permissions_config")
        if permissions_config and permissions_config.superuser_bypass:
            if getattr(user, "is_superuser", False) or getattr(user, "admin", False):
                return

        resolver = connection.app.state.get("permissions_resolver")
        if resolver is None:
            raise PermissionDeniedException("Permissions system not configured")

        db = connection.app.state.get("db_session")
        if db is None:
            raise PermissionDeniedException("db_session not found in app state")

        # Resolve resource scope from path params
        resource_type = None
        resource_id = None
        if resource_id_param:
            resource_id = connection.path_params.get(resource_id_param)
            if resource_type_param:
                resource_type = connection.path_params.get(resource_type_param)
            # If no explicit type param, try to infer from the permissions config hierarchy
            elif resource_id and permissions_config:
                # Use the first permission's prefix as resource type hint
                # e.g. "application:deploy" -> "application"
                for perm in permissions:
                    if ":" in perm:
                        resource_type = perm.split(":")[0]
                        break

        for perm in permissions:
            if not resolver.can(user.id, perm, resource_type, resource_id, db=db):
                raise PermissionDeniedException(f"Missing permission: {perm}")

    return guard


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
    """

    async def guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
        user = connection.scope.get("user")
        if user is None:
            raise NotAuthorizedException("Authentication required")

        permissions_config = connection.app.state.get("permissions_config")
        if permissions_config and permissions_config.superuser_bypass:
            if getattr(user, "is_superuser", False) or getattr(user, "admin", False):
                return

        from sqlalchemy import and_, or_, select

        db = connection.app.state.get("db_session")
        if db is None:
            raise PermissionDeniedException("db_session not found in app state")

        models = connection.app.state.get("permissions_models")
        if not models:
            raise PermissionDeniedException("Permissions system not configured")

        UserRoleAssignment = models["UserRoleAssignment"]
        Role = models["Role"]

        resource_type = None
        resource_id = None
        if resource_id_param:
            resource_id = connection.path_params.get(resource_id_param)
            if resource_type_param:
                resource_type = connection.path_params.get(resource_type_param)

        stmt = (
            select(Role.name)
            .join(UserRoleAssignment, UserRoleAssignment.role_id == Role.id)
            .where(UserRoleAssignment.user_id == user.id)
            .where(Role.name.in_(role_names))
        )

        scope_filters = [
            and_(
                UserRoleAssignment.resource_type.is_(None),
                UserRoleAssignment.resource_id.is_(None),
            )
        ]
        if resource_type and resource_id:
            scope_filters.append(
                and_(
                    UserRoleAssignment.resource_type == resource_type,
                    UserRoleAssignment.resource_id == resource_id,
                )
            )

        stmt = stmt.where(or_(*scope_filters))
        result = db.execute(stmt).first()
        if result is None:
            raise PermissionDeniedException(f"Required role: {' or '.join(role_names)}")

    return guard
