from fastapi import Request, Depends, HTTPException, status

from src.entity.models import Role, User
from src.services.auth import auth_service


class RoleAccess:
    def __init__(self, allowed_roles: list[Role]):
        """
        Initializes the RoleAccess dependency.

        :param: allowed_roles (list): A list of `Role` objects that are allowed access to
                                   the resource. Each role must be an instance of the `Role` class
        """
        self.allowed_roles = allowed_roles

    async def __call__(self, request: Request, user: User = Depends(auth_service.get_current_user)):
        """
        Checks if the user's role is allowed to access the resource.

        :param self: Refers to the instance of the class
        :param request: str: The incoming HTTP request
        :param user:  The current user object
        :raise: exeption HTTP_403_FORBIDDEN: If the user's role is not in the `allowed_roles` list
        :return: None: The purpose of this method is to validate the user's role.
        """
        
        print(user.role, self.allowed_roles)
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="FORBIDDEN"
            )