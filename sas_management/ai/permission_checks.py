from typing import Set

from flask import current_app

from sas_management.models import Permission, RolePermission


def _user_is_admin(user) -> bool:
    return bool(user and getattr(user, "is_admin", False))


def _get_user_role_ids(user) -> Set[int]:
    role_ids: Set[int] = set()
    if not user:
        return role_ids

    # New-style many-to-many roles
    try:
        roles_rel = getattr(user, "roles", None)
        if roles_rel is not None:
            for role in roles_rel:  # dynamic relationship is iterable
                rid = getattr(role, "id", None)
                if rid is not None:
                    role_ids.add(rid)
    except Exception:
        pass

    # Legacy single role_obj
    try:
        role_obj = getattr(user, "role_obj", None)
        rid = getattr(role_obj, "id", None) if role_obj is not None else None
        if rid is not None:
            role_ids.add(rid)
    except Exception:
        pass

    return role_ids


def _has_ai_permission(user, permission_key: str) -> bool:
    """
    Check if a user has a specific ai:* permission.

    Rules:
    - Admin users always True
    - If Permission(ai:<key>) does not exist → do NOT block (feature not configured)
    - Otherwise, require at least one RolePermission for user's roles
    - Fail closed (False) on unexpected errors
    """
    if not user:
        return False

    if _user_is_admin(user):
        return True

    try:
        code = f"ai:{permission_key}"
        perm = Permission.query.filter_by(code=code).first()
        if not perm:
            # Permission not yet configured – do not auto-disable AI.
            return True

        role_ids = _get_user_role_ids(user)
        if not role_ids:
            return False

        exists = (
            RolePermission.query.filter(
                RolePermission.role_id.in_(list(role_ids)),
                RolePermission.permission_id == perm.id,
            ).count()
            > 0
        )
        return exists
    except Exception as e:  # pragma: no cover - defensive
        try:
            current_app.logger.warning(
                "AI permission check error for user_id=%s, key=%s: %s",
                getattr(user, "id", None),
                permission_key,
                e,
            )
        except Exception:
            pass
        return False


def can_use_ai_chat(user) -> bool:
    return _has_ai_permission(user, "ai_chat")


def can_use_ai_actions(user) -> bool:
    return _has_ai_permission(user, "ai_actions")


def can_use_ai_analytics(user) -> bool:
    return _has_ai_permission(user, "ai_analytics")


def can_use_ai_voice(user) -> bool:
    return _has_ai_permission(user, "ai_voice")


def can_use_ai_memory(user) -> bool:
    return _has_ai_permission(user, "ai_memory")


def can_use_ai_scheduling(user) -> bool:
    return _has_ai_permission(user, "ai_scheduling")


