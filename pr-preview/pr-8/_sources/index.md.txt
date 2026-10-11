# litestar-permissions

Fine-grained hierarchical RBAC for Litestar applications.

Roles are scoped to resources (an org, a project, an app) and permissions inherit upward through the hierarchy. A user with `org-admin` on Organization X automatically has those permissions on every project and application inside it.

Built on SQLAlchemy 2.x. Ships as a Litestar plugin with guards, middleware, and dynamic model generation.

## Installation

`````{tab-set}
````{tab-item} uv
```bash
uv add litestar-permissions
```
````

````{tab-item} pip
```bash
pip install litestar-permissions
```
````
`````

## Quick Start

```python
from litestar import Litestar, get
from litestar_permissions import PermissionsPlugin, PermissionsConfig, require_permission
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


config = PermissionsConfig(
    hierarchy={"application": "project", "project": "organization"},
)


@get(
    "/apps/{app_id:str}/deploy",
    guards=[require_permission("application:deploy", resource_id_param="app_id")],
)
async def deploy(app_id: str) -> dict:
    return {"status": "deploying"}


app = Litestar(
    route_handlers=[deploy],
    plugins=[PermissionsPlugin(config=config, base=Base)],
)
```

The plugin generates four SQLAlchemy tables (`roles`, `permissions`, `role_permissions`, `user_role_assignments`) bound to your `Base`. The resolver handles permission checks with an LRU cache and hierarchy traversal.

---

::::{grid} 1 2 2 3
:gutter: 3

:::{grid-item-card} Getting Started
:link: getting-started
:link-type: doc

Set up the plugin, define your hierarchy, and run your first permission check.
:::

:::{grid-item-card} Hierarchy & Scoping
:link: hierarchy
:link-type: doc

How resource hierarchies work and how permissions inherit between levels.
:::

:::{grid-item-card} Guards
:link: guards
:link-type: doc

Protect route handlers with `require_permission` and `require_role` guards.
:::

:::{grid-item-card} API Reference
:link: api/index
:link-type: doc

Full API docs for all public classes, functions, and protocols.
:::
::::

```{toctree}
:maxdepth: 2
:hidden:
:caption: Learn

getting-started
hierarchy
guards
```

```{toctree}
:maxdepth: 2
:hidden:
:caption: Reference

api/index
changelog
```

```{toctree}
:hidden:
:caption: Project

GitHub <https://github.com/JacobCoffee/litestar-permissions>
Discord <https://discord.gg/litestar-919193495116337154>
```
