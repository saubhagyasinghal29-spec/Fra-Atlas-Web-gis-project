"""Default role -> permission grants. Idempotent; safe to re-run."""
from apps.accounts.models import RolePermission
from apps.common.enums import Designation as D
from apps.common.enums import Permission as P

DEFAULT_GRANTS = {
    D.FIELD_OFFICER: [P.VIEW_CLAIM, P.CREATE_CLAIM, P.EDIT_CLAIM, P.SUBMIT_CLAIM],
    D.BLOCK_OFFICIAL: [P.VIEW_CLAIM, P.EDIT_CLAIM, P.SUBMIT_CLAIM, P.REVIEW_CLAIM],
    D.DISTRICT_ADMIN: [P.VIEW_CLAIM, P.EDIT_CLAIM, P.REVIEW_CLAIM, P.APPROVE_CLAIM,
                       P.REJECT_CLAIM, P.VIEW_ANALYTICS],
    D.STATE_COORDINATOR: [P.VIEW_CLAIM, P.REVIEW_CLAIM, P.APPROVE_CLAIM,
                          P.REJECT_CLAIM, P.VIEW_ANALYTICS],
    D.ML_RESEARCHER: [P.VIEW_ANALYTICS],
    D.ML_SYSTEM: [P.VIEW_ANALYTICS],
}


def seed_role_permissions():
    created = 0
    for role, perms in DEFAULT_GRANTS.items():
        for perm in perms:
            _, was_created = RolePermission.objects.get_or_create(
                role=role, permission_code=perm
            )
            created += int(was_created)
    return created
