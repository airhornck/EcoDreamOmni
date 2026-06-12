"""RBAC helpers for task and publish resource access control.

Aligned with PRD V2.6 §10.11 — Phase 3 role-based permissions.

Roles:
  admin    — full access to all tasks and reviews.
  reviewer — can review any task in human_wait; otherwise same as operator.
  operator — can only view/operate tasks they created.
"""

from src.models.user import User


def is_admin(user: User) -> bool:
    return user.role == "admin"


def can_view_task(user: User, task) -> bool:
    """Check if user can view a specific task."""
    if is_admin(user):
        return True
    return task.created_by == user.id


def can_modify_task(user: User, task) -> bool:
    """Check if user can update/delete/transition a task."""
    if is_admin(user):
        return True
    return task.created_by == user.id


def can_review_task(user: User, task) -> bool:
    """Check if user can approve/reject/revise a task.

    admin & reviewer can review any task in human_wait.
    operator can only review their own tasks.
    """
    if is_admin(user):
        return True
    if user.role == "reviewer":
        return True
    return task.created_by == user.id


def can_view_publish_task(user: User, publish_task) -> bool:
    """Check if user can view a publish task."""
    if is_admin(user):
        return True
    return publish_task.created_by == user.id


def can_modify_publish_task(user: User, publish_task) -> bool:
    """Check if user can update/delete/execute a publish task."""
    if is_admin(user):
        return True
    return publish_task.created_by == user.id


def task_list_created_by_filter(user: User) -> str | None:
    """Return created_by value for list queries.

    admin   → None (no filter, view all)
    others  → user.id (view only own tasks)
    """
    if is_admin(user):
        return None
    return user.id
