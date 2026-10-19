from fastapi import Depends,HTTPException,status
from app.core.enum import UserRole
from app.dependencies.auth_dep import get_current_user
from app.models.users import User


def require_roles(*allowed_roles: UserRole):
    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in [
            role.value for role in allowed_roles
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this resource",
            )

        return current_user

    return role_checker