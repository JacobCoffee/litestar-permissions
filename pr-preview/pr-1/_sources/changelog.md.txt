# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025

### Features

- Initial extraction from ancla workspace
- Hierarchical RBAC with resource scoping
- SQLAlchemy model generation via `create_models()` factory
- `PermissionResolver` with LRU cache and hierarchy traversal
- `require_permission` and `require_role` Litestar guards
- `PermissionsMiddleware` for injecting permissions into request scope
- `PermissionsPlugin` for Litestar `InitPluginProtocol` integration
