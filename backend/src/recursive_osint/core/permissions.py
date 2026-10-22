"""
Role-based permissions and access control.
"""

from enum import Enum
from typing import Set


class UserRole(str, Enum):
    ADMIN = "admin"
    INVESTIGATOR = "investigator"
    ANALYST = "analyst"
    VIEWER = "viewer"


class Permission(str, Enum):
    INVESTIGATION_CREATE = "investigation:create"
    INVESTIGATION_READ = "investigation:read"
    INVESTIGATION_UPDATE = "investigation:update"
    INVESTIGATION_DELETE = "investigation:delete"
    INVESTIGATION_RUN = "investigation:run"
    INVESTIGATION_EXPORT = "investigation:export"
    EVIDENCE_CREATE = "evidence:create"
    EVIDENCE_READ = "evidence:read"
    SOURCES_VIEW = "sources:view"
    SETTINGS_MANAGE = "settings:manage"
    USERS_MANAGE = "users:manage"


ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: set(Permission),
    UserRole.INVESTIGATOR: {
        Permission.INVESTIGATION_CREATE,
        Permission.INVESTIGATION_READ,
        Permission.INVESTIGATION_UPDATE,
        Permission.INVESTIGATION_RUN,
        Permission.INVESTIGATION_EXPORT,
        Permission.EVIDENCE_CREATE,
        Permission.EVIDENCE_READ,
        Permission.SOURCES_VIEW,
    },
    UserRole.ANALYST: {
        Permission.INVESTIGATION_READ,
        Permission.INVESTIGATION_EXPORT,
        Permission.EVIDENCE_READ,
        Permission.SOURCES_VIEW,
    },
    UserRole.VIEWER: {
        Permission.INVESTIGATION_READ,
        Permission.EVIDENCE_READ,
    },
}


def has_permission(role: UserRole, permission: Permission) -> bool:
    """Checks if a given role has the requested permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())
