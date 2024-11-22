from fastapi import Depends
from libgravatar import Gravatar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User
from src.schemas import UserModel


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):

    """
    The get_user_by_email function retrieves a user by its email.

        :param email: str: The email of the user to search for
        :param db: AsyncSession, optional: The asynchronous database session used to query the database 
               Defaults to `Depends(get_db)` to automatically manage the session

        :return: User's information| None: The `User` object if a match is found, otherwise `None`
    """

    stmt = select(User).filter(User.email == email)
    result = await db.execute(stmt)
    user = await result.scalar_one_or_none()
    return user


async def create_user(body: UserModel, db: AsyncSession = Depends(get_db)):

    """
    The create_user function creates ands retrieves new user and his details.

        :param body: UserModel, Pass the user data to be created 
        :param db: AsyncSession, optional: The asynchronous database session used to query the database 
               Defaults to `Depends(get_db)` to automatically manage the session
        :return: The `new_user` object 
    """

    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)

    new_user = User(  # new_user = User(**body.model_dump(), avatar=avatar)
        username=body.username, email=body.email, password=body.password, avatar=avatar
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: AsyncSession) -> None:
    """
    The update_token function update the refresh token for the specified user.

    :param user: The user object to update
    :param token: The new refresh token to assign, or None to remove the token
    :param db: AsyncSession: The database session
    :return: None
    """
    user.refresh_token = token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession) -> None:
    """
    The confirmed_email function Confirm the user's email address.

    :param email: The user's email address
    :param db: The database session
    :return: None
    """

    user = await get_user_by_email(email, db)
    if user is None:
        raise ValueError(f"User with email {email} not found")
    user.confirmed = True
    await db.commit()


async def update_avatar_url(email: str, url: str | None, db: AsyncSession) -> User:
    """
    The update_avatar_url function update the user's avatar URL by users's email.

    :param email: str.: The user's email address
    :param db: AsyncSession: The database session
    :return: The updated user object
    """

    user = await get_user_by_email(email, db)
    if user is None:
        raise ValueError("User not found")
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user
