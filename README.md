# litestar-permissions

[![CI](https://github.com/JacobCoffee/litestar-permissions/actions/workflows/ci.yml/badge.svg)](https://github.com/JacobCoffee/litestar-permissions/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/litestar-permissions.svg)](https://badge.fury.io/py/litestar-permissions)
[![Python versions](https://img.shields.io/pypi/pyversions/litestar-permissions.svg)](https://pypi.org/project/litestar-permissions/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Fine-grained hierarchical RBAC for Litestar applications.

Roles are scoped to resources and permissions inherit upward through the hierarchy. An `org-admin` role on Organization X grants those permissions on every project and application inside it. Built on SQLAlchemy 2.x, ships as a Litestar plugin.

## Installation

```bash
uv add litestar-permissions
```

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

The plugin generates four SQLAlchemy tables (`roles`, `permissions`, `role_permissions`, `user_role_assignments`) bound to your `Base`. Guards check permissions at the resource scope, walking up the hierarchy to find matching role assignments.

## How the Hierarchy Works

Define parent-child relationships between resource types:

```python
PermissionsConfig(
    hierarchy={
        "application": "project",   # application's parent is project
        "project": "organization",   # project's parent is organization
    }
)
```

When checking `application:deploy` on a specific app, the resolver checks role assignments scoped to that app, then its parent project, then the parent org, then global. A match at any level grants the permission.

## Development

```bash
make dev           # install with all dev deps
make test          # run tests
make lint          # run prek hooks (ruff, ty, codespell)
make docs-serve    # live-reload docs on localhost:8001
```

## Documentation

Full docs at [jacobcoffee.github.io/litestar-permissions](https://jacobcoffee.github.io/litestar-permissions).

## License

MIT - see [LICENSE](LICENSE).
