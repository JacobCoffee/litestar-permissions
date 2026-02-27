from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.plugins import InitPluginProtocol

from litestar_permissions.config import PermissionsConfig
from litestar_permissions.models import create_models
from litestar_permissions.resolver import PermissionResolver

if TYPE_CHECKING:
    from litestar.config.app import AppConfig
    from sqlalchemy.orm import DeclarativeBase


class PermissionsPlugin(InitPluginProtocol):
    """Litestar plugin for fine-grained hierarchical RBAC.

    Example::

        from litestar_permissions import PermissionsPlugin, PermissionsConfig

        config = PermissionsConfig(
            hierarchy={"application": "project", "project": "organization"},
        )

        app = Litestar(
            plugins=[PermissionsPlugin(config=config, base=Base)],
        )
    """

    def __init__(
        self,
        config: PermissionsConfig | None = None,
        base: type[DeclarativeBase] | None = None,
    ) -> None:
        self.config = config or PermissionsConfig()
        self.base = base
        self.models: dict[str, type] = {}
        self.resolver: PermissionResolver | None = None

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        if self.base is not None:
            self.models = create_models(self.base, self.config.table_prefix)

        self.resolver = PermissionResolver(config=self.config, models=self.models)

        # Store in app state for guards and middleware to access
        app_config.state.update(
            {
                "permissions_config": self.config,
                "permissions_models": self.models,
                "permissions_resolver": self.resolver,
            }
        )

        return app_config
