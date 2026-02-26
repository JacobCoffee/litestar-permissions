from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# Sentinel classes for re-export from __init__.py
class Role:
    """Named role that groups permissions. Use create_models() to get concrete ORM classes."""

    pass


class Permission:
    """A granular action like 'application:deploy'. Use create_models() to get concrete ORM classes."""

    pass


class RolePermission:
    """Many-to-many: which permissions belong to which role. Use create_models() to get concrete ORM classes."""

    pass


class UserRoleAssignment:
    """Assigns a role to a user, optionally scoped to a resource. Use create_models() to get concrete ORM classes."""

    pass


def create_models(base: type[DeclarativeBase], table_prefix: str = "") -> dict[str, type]:
    """Factory that creates concrete RBAC models bound to the app's Base.

    Returns dict with keys: 'Role', 'Permission', 'RolePermission', 'UserRoleAssignment'
    """

    class Permission(base):
        """A granular action like 'application:deploy' or 'config:write'."""

        __tablename__ = f"{table_prefix}permissions"

        id: Mapped[str] = mapped_column(Uuid(), primary_key=True, default=uuid4)
        codename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
        description: Mapped[str | None] = mapped_column(Text(), nullable=True)
        created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

        role_permissions: Mapped[list[RolePermission]] = relationship(back_populates="permission")

        def __repr__(self) -> str:
            return f"<Permission {self.codename}>"

    class Role(base):
        """Named set of permissions, e.g. 'org-admin', 'project-viewer'."""

        __tablename__ = f"{table_prefix}roles"

        id: Mapped[str] = mapped_column(Uuid(), primary_key=True, default=uuid4)
        name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
        description: Mapped[str | None] = mapped_column(Text(), nullable=True)
        created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

        role_permissions: Mapped[list[RolePermission]] = relationship(
            back_populates="role", cascade="all, delete-orphan"
        )
        assignments: Mapped[list[UserRoleAssignment]] = relationship(
            back_populates="role", cascade="all, delete-orphan"
        )

        def __repr__(self) -> str:
            return f"<Role {self.name}>"

    class RolePermission(base):
        """Many-to-many: which permissions belong to which role."""

        __tablename__ = f"{table_prefix}role_permissions"

        role_id: Mapped[str] = mapped_column(
            Uuid(), ForeignKey(f"{table_prefix}roles.id", ondelete="CASCADE"), primary_key=True
        )
        permission_id: Mapped[str] = mapped_column(
            Uuid(), ForeignKey(f"{table_prefix}permissions.id", ondelete="CASCADE"), primary_key=True
        )

        role: Mapped[Role] = relationship(back_populates="role_permissions")
        permission: Mapped[Permission] = relationship(back_populates="role_permissions")

    class UserRoleAssignment(base):
        """Assigns a role to a user, optionally scoped to a resource."""

        __tablename__ = f"{table_prefix}user_role_assignments"
        __table_args__ = (
            UniqueConstraint(
                "user_id", "role_id", "resource_type", "resource_id", name=f"uq_{table_prefix}user_role_resource"
            ),
        )

        id: Mapped[str] = mapped_column(Uuid(), primary_key=True, default=uuid4)
        user_id: Mapped[str] = mapped_column(Uuid(), nullable=False, index=True)
        role_id: Mapped[str] = mapped_column(
            Uuid(), ForeignKey(f"{table_prefix}roles.id", ondelete="CASCADE"), nullable=False
        )

        # Resource scoping (nullable = global assignment)
        resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
        resource_id: Mapped[str | None] = mapped_column(Uuid(), nullable=True)

        created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

        role: Mapped[Role] = relationship(back_populates="assignments")

        def __repr__(self) -> str:
            scope = f"{self.resource_type}:{self.resource_id}" if self.resource_type else "global"
            return f"<UserRoleAssignment user={self.user_id} role={self.role_id} scope={scope}>"

    return {
        "Permission": Permission,
        "Role": Role,
        "RolePermission": RolePermission,
        "UserRoleAssignment": UserRoleAssignment,
    }
