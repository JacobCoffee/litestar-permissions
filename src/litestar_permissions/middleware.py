from typing import ClassVar

from litestar.middleware import AbstractMiddleware
from litestar.types import Receive, Scope, Send


class PermissionsMiddleware(AbstractMiddleware):
    """Injects the user's resolved permissions into request scope for template use.

    Note:
        Consumers must populate ``scope["db_session"]`` with a per-request
        ``AsyncSession`` before this middleware runs (e.g. via an earlier middleware).
    """

    scopes: ClassVar[set[str]] = {"http"}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        config = scope["app"].state.get("permissions_config")
        user_key = config.user_key if config else "user"
        user = scope.get(user_key)
        if user is not None:
            resolver = scope["app"].state.get("permissions_resolver")
            if resolver:
                db = scope.get("db_session")
                if db is None:
                    scope["permissions"] = set()
                    await self.app(scope, receive, send)
                    return
                perms = await resolver.get_user_permissions(user.id, db=db)
                scope["permissions"] = perms
            else:
                scope["permissions"] = set()
        else:
            scope["permissions"] = set()

        await self.app(scope, receive, send)
