# Hierarchy & Scoping

The core idea: permissions flow upward through a resource tree. A role assigned at an organization grants those permissions on every project and application under it.

## Defining the Hierarchy

Pass a dict mapping each child type to its parent type:

```python
PermissionsConfig(
    hierarchy={
        "application": "project",
        "project": "organization",
    }
)
```

This creates the chain: `application` -> `project` -> `organization`.

When checking if a user can `application:deploy` on a specific application, the resolver:

1. Checks role assignments scoped to that application
2. Walks up to the parent project and checks there
3. Walks up to the parent organization and checks there
4. Checks global (unscoped) role assignments

A match at any level grants the permission.

## Resource Resolver

The hierarchy traversal needs to know how to find a resource's parent. Provide a `resource_resolver` callback:

```python
def resolve_resource(resource_type: str, resource_id: str, db: Session):
    """Look up a resource and return an object with a .parent attribute."""
    if resource_type == "application":
        return db.get(Application, resource_id)
    elif resource_type == "project":
        return db.get(Project, resource_id)
    return None


config = PermissionsConfig(
    hierarchy={"application": "project", "project": "organization"},
    resource_resolver=resolve_resource,
)
```

The returned object must satisfy `ResourceProtocol`:

```python
class ResourceProtocol(Protocol):
    id: UUID | str | int
    resource_type: str
    parent: ResourceProtocol | None  # None = top of the tree
```

Without a `resource_resolver`, hierarchy traversal stops at the direct scope. Global assignments still apply.

## Scoped vs Global Assignments

A `UserRoleAssignment` with `resource_type=None` and `resource_id=None` is global. The role applies everywhere.

A scoped assignment ties the role to a specific resource:

```python
# Global admin
UserRoleAssignment(user_id=user.id, role_id=admin_role.id)

# Admin only for organization X
UserRoleAssignment(
    user_id=user.id,
    role_id=admin_role.id,
    resource_type="organization",
    resource_id=org_x.id,
)
```

## Caching

The resolver caches permission check results with an LRU strategy. Defaults:

- `cache_ttl`: 300 seconds
- `cache_max_size`: 10,000 entries

Invalidate after role changes:

```python
resolver = app.state["permissions_resolver"]
resolver.invalidate_user(user.id)   # clear one user
resolver.invalidate_all()            # clear everything
```

Set `cache_ttl=0` to disable caching entirely.
