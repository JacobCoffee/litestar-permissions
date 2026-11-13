# Getting Started

## Prerequisites

- Python 3.12+
- A Litestar application
- SQLAlchemy 2.x with a `DeclarativeBase`

## Install

```{eval-rst}
.. tab-set::
    :class: outline

    .. tab-item:: :iconify:`material-icon-theme:uv` uv

        .. code-block:: bash

            uv add litestar-permissions

    .. tab-item:: :iconify:`devicon:pypi` pip

        .. code-block:: bash

            pip install litestar-permissions
```

## Set Up the Plugin

The plugin needs two things: a `PermissionsConfig` and your SQLAlchemy `Base`.

```python
from litestar import Litestar
from litestar_permissions import PermissionsPlugin, PermissionsConfig
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


config = PermissionsConfig(
    hierarchy={"application": "project", "project": "organization"},
)

app = Litestar(
    plugins=[PermissionsPlugin(config=config, base=Base)],
)
```

On startup, the plugin calls `create_models(Base)` and generates four tables:

| Table | Purpose |
|-------|---------|
| `permissions` | Granular actions like `application:deploy` or `config:write` |
| `roles` | Named groups of permissions (`org-admin`, `project-viewer`) |
| `role_permissions` | Many-to-many linking roles to permissions |
| `user_role_assignments` | Assigns a role to a user, optionally scoped to a resource |

These get stored in `app.state` so guards and middleware can access them.

## Add a Guard

Protect a route handler by adding a guard:

```python
from litestar import get
from litestar_permissions import require_permission


@get(
    "/apps/{app_id:str}/deploy",
    guards=[require_permission("application:deploy", resource_id_param="app_id")],
)
async def deploy(app_id: str) -> dict:
    return {"status": "deploying"}
```

The guard reads the user from `connection.scope["user"]`, looks up their roles at the resource scope (and ancestor scopes), and raises `PermissionDeniedException` if they lack the permission.

## Provide a DB Session

Guards and middleware expect a SQLAlchemy `Session` in `app.state["db_session"]`. Wire that up however fits your app (dependency injection, middleware, lifespan handler).

## User Protocol

Your user model needs to satisfy `UserProtocol`:

```python
from uuid import UUID


class User:
    id: UUID       # or str or int
    is_superuser: bool
```

Superusers bypass all permission checks by default. Disable with `PermissionsConfig(superuser_bypass=False)`.

## What's Next

- [Hierarchy & Scoping](hierarchy.md) covers how permissions inherit through resource trees
- [Guards](guards.md) details `require_permission` and `require_role`
- [API Reference](api/index.md) for the full public API
