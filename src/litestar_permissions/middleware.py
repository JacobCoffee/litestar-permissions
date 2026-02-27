from typing import ClassVar

from litestar.middleware import AbstractMiddleware
from litestar.types import Receive, Scope, Send


class PermissionsMiddleware(AbstractMiddleware):
    """Injects the user's resolved permissions into request scope for template use."""

    scopes: ClassVar[set[str]] = {"http"}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        user = scope.get("user")
        if user is not None:
            resolver = scope["app"].state.get("permissions_resolver")
            if resolver:
                db = scope["app"].state.get("db_session")
                if db is None:
                    scope["permissions"] = set()
                    await self.app(scope, receive, send)
                    return
                perms = resolver.get_user_permissions(user.id, db=db)
                scope["permissions"] = perms
            else:
                scope["permissions"] = set()
        else:
            scope["permissions"] = set()

        await self.app(scope, receive, send)
