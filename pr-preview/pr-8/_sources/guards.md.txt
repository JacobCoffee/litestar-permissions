# Guards

Two guard factories ship with the plugin: `require_permission` and `require_role`. Both are Litestar guard functions you attach to route handlers.

## require_permission

Checks that the current user has **all** of the specified permissions.

```python
from litestar import get
from litestar_permissions import require_permission


@get(
    "/projects/{project_id:str}/settings",
    guards=[require_permission("project:settings:read", resource_id_param="project_id")],
)
async def project_settings(project_id: str) -> dict:
    ...
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `*permissions` | `str` | Permission codenames the user must have. All must match. |
| `resource_type_param` | `str \| None` | Path param name holding the resource type. |
| `resource_id_param` | `str \| None` | Path param name holding the resource ID. |

If `resource_type_param` is omitted, the guard infers the resource type from the permission prefix. `"application:deploy"` becomes resource type `"application"`.

### Multiple permissions

```python
guards=[require_permission("project:read", "project:settings:read", resource_id_param="project_id")]
```

The user must have both. If either is missing, the guard raises `PermissionDeniedException`.

## require_role

Checks that the current user has **any** of the specified roles.

```python
from litestar import delete
from litestar_permissions import require_role


@delete(
    "/orgs/{org_id:str}",
    guards=[require_role("org-owner", "super-admin", resource_id_param="org_id")],
)
async def delete_org(org_id: str) -> None:
    ...
```

### Parameters

Same as `require_permission`, but `*role_names` instead of `*permissions`. The user needs at least one of the listed roles.

## Superuser Bypass

Both guards check for superuser status before hitting the database. If `PermissionsConfig.superuser_bypass` is `True` (the default), users with `is_superuser=True` or `admin=True` skip all checks.

## App State Requirements

Guards read from `app.state`:

- `permissions_config` - `PermissionsConfig` instance
- `permissions_resolver` - `PermissionResolver` instance
- `permissions_models` - dict of ORM model classes
- `db_session` - SQLAlchemy `Session`

The plugin sets up the first three automatically. You're responsible for providing `db_session`.
