from fastapi import APIRouter, Depends, Path, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

from typing import List

from src.database.db import get_db
from src.entity.models import User, Role
from src.schemas import ContactResponse, ContactSchema
from src.services.auth import auth_service
from src.repository import contacts as repository_contacts
from src.services.role import RoleAccess


router = APIRouter()
access_to_route_all = RoleAccess([Role.admin, Role.moderator])


@router.get("/")
def main_root():
    """
    The get function tests the startup of the application to ensure the application is running correctly.
    :return: A dictionary with a greeting message.
    """

    return {"message": "Hello, fastapi application from contact_router.py!"}


@router.post(
    "/contacts",
    dependencies=[Depends(RateLimiter(times=2, seconds=5))],
)
async def create_contact(
    body: ContactSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    The create_contact function creates a new contact.
    :param RateLimiter: Rate-limited to 1 request per 20 seconds.
    :param body: ContactSchema,: Pass the contact data to be created
    :param db: AsyncSession: Pass the database session dependency
    :param user: User: Get the currently authenticated user
    :return: A contact object
    """

    return await repository_contacts.create_contact(body, db, user)  # user_id


@router.get(
    "/contacts/all",
    response_model=list[ContactResponse],
    dependencies=[
        Depends(access_to_route_all),
        Depends(RateLimiter(times=1, seconds=20)),
    ],
)
async def get_all_contacts(
    limit: int = Query(default=10),
    offset: int = Query(default=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    The get_all_contacts function retrieves all contacts with pagination support from the database.

    :param Depends(access_to_route_all): This ensures that only authorized users can access this route.
    :param Depends(RateLimiter): Rate-limited to 1 request per 20 seconds.
    :param limit: int: Limit the number of contacts returned
    :param offset: int: Determine how many records to skip
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Ensure that the user making the request is authorized to do
    :return: list[ContactResponse]: A list of `Contact` objects
    """

    return await repository_contacts.get_all_contacts(limit, offset, db)


@router.get("/contacts/id/{contact_id}", response_model=ContactResponse)
async def get_contact_by_id(
    limit: int = Query(default=10),
    offset: int = Query(default=0),
    contact_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    The get_contact_by_id function retrieves a contact  by its ID with pagination support from the database.

    :param limit: int: Limit the number of contacts returned
    :param offset: int: Determine how many records to skip
    :param contact_id: int: Specify the id of the contact to retrieve
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Ensure that the user making the request is authorized to do
    :return: A ContactResponse object
    """

    contact = await repository_contacts.get_contact_by_id(limit, offset, contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contact


@router.get("/contacts/by_name/{contact_fullname}", response_model=ContactResponse)
async def get_contact_by_fullname(
    limit: int = Query(default=10),
    offset: int = Query(default=0),
    contact_fullname: str = Path(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    The get_contact_by_fullname function retrieves a contact by its fullname with pagination support from the database.

    :param limit: int: Limit the number of contacts returned
    :param offset: int: Determine how many records to skip
    :param contact_fullname: int: Specify the contact_fullname of the contact to retrieve
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Ensure that the user making the request is authorized to do
    :return: A ContactResponse object
    """

    contact = await repository_contacts.get_contact_by_fullname(
        limit, offset, contact_fullname, db, user
    )
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.get("/contacts/by_email/{contact_email}", response_model=ContactResponse)
async def get_contact_by_email(
    limit: int = Query(default=10),
    offset: int = Query(default=0),
    contact_email: str = Path(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    The get_contact_by_fullname function retrieves a contact by its email with pagination support from the database.

    :param limit: int: Limit the number of contacts returned
    :param offset: int: Determine how many records to skip
    :param contact_email: int: Specify the contact_fullname of the contact to retrieve
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Ensure that the user making the request is authorized to do
    :return: A ContactResponse object
    """

    return await repository_contacts.get_contact_by_email(
        limit, offset, contact_email, db, user
    )


@router.get(
    "/contacts/by_birthday/{get_birthday}", response_model=list[ContactResponse]
)
async def get_upcoming_birthdays(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    The get_upcoming_birthdays function retrieves a list of birthsdays during nearest 7 days from today from the database.

    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Ensure that the user making the request is authorized to do
    :return: list[ContactResponse]: A list of ContactResponse objects
    """

    return await repository_contacts.get_upcoming_birthdays(db, user)


@router.get("/contacts/get_new_day/{new_date}", response_model=list[ContactResponse])
async def get_upcoming_birthdays_from_new_date(
    new_date: str = Path(..., description="Current date in format YYYY-MM-DD"),
    limit: int = Query(default=10),
    offset: int = Query(default=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    The get_upcoming_birthdays_from_new_date function retrieves a list of birthsdays during nearest 7 days
    from new today from the database with pagination support.

    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Ensure that the user making the request is authorized to do
    :return: list[ContactResponse]: A list of ContactResponse objects
    """

    return await repository_contacts.get_upcoming_birthdays_from_new_date(
        new_date, limit, offset, db, user
    )


@router.put("/contacts/update/{contact_id}")
async def update_contact(
    body: ContactSchema,
    contact_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    The update_contact function updates a contact with the given contact_id using the provided ContactSchema body.

    :param body: ContactSchema: Pass the updated contact information to the function
    :param contact_id: int: Identify the contact to be deleted
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the current authenticated user
    :return: A contactresponse object
    """

    contact = await repository_contacts.update_contact(body, contact_id, db, user)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.delete("/contacts/delete/{contact_id}", response_model=dict)
async def delete_contact(
    contact_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    The delete_contact function deletes a contact with the given contact_id.

    :param contact_id: int: Identify the contact to be deleted
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the current authenticated user
    :return: The massage with information about succefull deleting of the contact.
    :raise: HTTPException: If the contact is not found raises a 404 error.
    """

    result = await repository_contacts.delete_contact(contact_id, db)
    return result
