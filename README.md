# litestar-permissions

Fine-grained hierarchical RBAC for Litestar applications.

## Installation

```bash
pip install litestar-permissions
```

## Quick Start

```python
from litestar import Litestar, get
from litestar_permissions import PermissionsPlugin, PermissionsConfig, require_permission

config = PermissionsConfig(
    hierarchy={"application": "project", "project": "organization"},
)

@get("/apps/{app_id}/deploy", guards=[require_permission("application:deploy", resource_id_param="app_id")])
async def deploy(app_id: str) -> dict:
    return {"status": "deploying"}

app = Litestar(
    route_handlers=[deploy],
    plugins=[PermissionsPlugin(config=config, base=Base)],
)
```
