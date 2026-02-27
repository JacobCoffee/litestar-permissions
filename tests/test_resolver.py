from uuid import uuid4

from litestar_permissions.config import PermissionsConfig
from litestar_permissions.resolver import PermissionResolver


async def test_resolver_global_permission(db_session, rbac_models):
    """User with a global role can access the permission."""
    Role = rbac_models["Role"]
    Permission = rbac_models["Permission"]
    RolePermission = rbac_models["RolePermission"]
    UserRoleAssignment = rbac_models["UserRoleAssignment"]

    user_id = uuid4()

    # Create role and permission
    role = Role(name="admin")
    perm = Permission(codename="application:deploy")
    db_session.add_all([role, perm])
    await db_session.flush()

    rp = RolePermission(role_id=role.id, permission_id=perm.id)
    assignment = UserRoleAssignment(user_id=user_id, role_id=role.id)
    db_session.add_all([rp, assignment])
    await db_session.commit()

    config = PermissionsConfig()
    resolver = PermissionResolver(config=config, models=rbac_models)

    assert await resolver.can(user_id, "application:deploy", db=db_session) is True
    assert await resolver.can(user_id, "nonexistent:perm", db=db_session) is False


async def test_resolver_scoped_permission(db_session, rbac_models):
    """User with a resource-scoped role can access permission for that resource."""
    Role = rbac_models["Role"]
    Permission = rbac_models["Permission"]
    RolePermission = rbac_models["RolePermission"]
    UserRoleAssignment = rbac_models["UserRoleAssignment"]

    user_id = uuid4()
    org_id = uuid4()

    role = Role(name="org-admin")
    perm = Permission(codename="project:create")
    db_session.add_all([role, perm])
    await db_session.flush()

    rp = RolePermission(role_id=role.id, permission_id=perm.id)
    assignment = UserRoleAssignment(
        user_id=user_id,
        role_id=role.id,
        resource_type="organization",
        resource_id=org_id,
    )
    db_session.add_all([rp, assignment])
    await db_session.commit()

    config = PermissionsConfig()
    resolver = PermissionResolver(config=config, models=rbac_models)

    # Has permission for this specific org
    assert await resolver.can(user_id, "project:create", "organization", org_id, db=db_session) is True
    # Does NOT have permission for a different org
    assert await resolver.can(user_id, "project:create", "organization", uuid4(), db=db_session) is False


async def test_resolver_caching(db_session, rbac_models):
    """Results are cached and can be invalidated."""
    Role = rbac_models["Role"]
    Permission = rbac_models["Permission"]
    RolePermission = rbac_models["RolePermission"]
    UserRoleAssignment = rbac_models["UserRoleAssignment"]

    user_id = uuid4()

    role = Role(name="viewer")
    perm = Permission(codename="app:view")
    db_session.add_all([role, perm])
    await db_session.flush()

    rp = RolePermission(role_id=role.id, permission_id=perm.id)
    assignment = UserRoleAssignment(user_id=user_id, role_id=role.id)
    db_session.add_all([rp, assignment])
    await db_session.commit()

    config = PermissionsConfig(cache_ttl=300)
    resolver = PermissionResolver(config=config, models=rbac_models)

    # First call populates cache
    assert await resolver.can(user_id, "app:view", db=db_session) is True
    assert len(resolver._cache) == 1

    # Invalidate
    resolver.invalidate_user(user_id)
    assert len(resolver._cache) == 0
