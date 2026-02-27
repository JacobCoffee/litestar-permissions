from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class UserProtocol(Protocol):
    """Interface that user models must satisfy for permission resolution."""

    @property
    def id(self) -> UUID | str | int: ...

    @property
    def is_superuser(self) -> bool: ...


@runtime_checkable
class ResourceProtocol(Protocol):
    """Interface for resources that permissions can be scoped to."""

    @property
    def id(self) -> UUID | str | int: ...

    @property
    def resource_type(self) -> str:
        """e.g. 'organization', 'project', 'application'"""
        ...

    @property
    def parent(self) -> ResourceProtocol | None:
        """Parent resource for hierarchy traversal. None = top-level."""
        ...
