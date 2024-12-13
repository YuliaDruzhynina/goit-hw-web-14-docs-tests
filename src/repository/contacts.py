from datetime import date, datetime, timedelta
from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.database.db import get_db
from src.entity.models import Contact, User
from src.schemas import ContactSchema
from src.services.auth import auth_service


async def create_contact(body: ContactSchema, db: AsyncSession, user: User):
    """
    The create_contact function create a new contact in a database.

    :param body: ContactSchema: The data for the contact to be created
    :param db: AsyncSession: The asynchronous database session used to execute the query and perform the commit
    :param user: User: Get the current authenticated user. Used to ensure the contact is created for the correct user.
    :raise: HTTP_409_CONFLICT: If contact already exists
    :return: Contact: The created contact object with all fields populated, including the generated ID from the database
    """

    contact = await db.execute(
        select(Contact).filter(Contact.email == body.email, Contact.user == user)
    )
    existing_contact = contact.scalar_one_or_none()
    if existing_contact:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Contact already exists!"
        )
    contact = Contact(
        fullname=body.fullname,
        phone_number=body.phone_number,
        email=body.email,
        birthday=body.birthday,
        user=user,
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def get_all_contacts(limit: int, offset: int, db: AsyncSession = Depends(get_db)):
    """
    The get_all_contacts function retrieves a list of contacts.

    :param limit: int: Limit the number of contacts returned
    :param offset: int: Determine how many records to skip
    :param db: AsyncSession, optional: The asynchronous database session used to query the database
               Defaults to `Depends(get_db)` to automatically manage the session
    :return: list[Contact]: A list of `Contact` objects matching the query based on `limit` and `offset`
    """
    stmt = select(Contact).limit(limit).offset(offset)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_contact_by_id(
    limit: int,
    offset: int,
    contact_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
):
    """
    The get_all_contact_by_id function retrieves a contact by its ID.

    :param limit: int: Limit the number of contacts returned
    :param offset: int: Determine how many records to skip
    :param db: AsyncSession, optional: The asynchronous database session used to query the database
           Defaults to `Depends(get_db)` to automatically manage the session
    :return: A contactresponse object
    """

    stmt = select(Contact).filter(Contact.id == contact_id).limit(limit).offset(offset)
    result = await db.execute(stmt)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    contact = result.scalar_one_or_none()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contact


async def get_contact_by_fullname(
    limit: int, offset: int, contact_fullname: str, db: AsyncSession, user: User
):
    """
    The get_all_contact_by_fullname function retrieves a contact by its fullname.

        :param limit: int: Limit the number of contacts returned
        :param offset: int: Determine how many records to skip
        :param contact_fullname: str: The fullname of the contact to search for
        :param db: AsyncSession, optional: The asynchronous database session used to query the database
               Defaults to `Depends(get_db)` to automatically manage the session
        :param user: User: Get the current authenticated user. 
        :return: Contact | None: The `Contact` object if a match is found, otherwise `None`
    """

    stmt = (
        select(Contact)
        .filter(Contact.user_id == user.id, Contact.fullname == contact_fullname)
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    return contact


async def get_contact_by_email(
    limit: int, offset: int, contact_email: str, db: AsyncSession, user: User
):
    """
    The get_all_contact_by_email function retrieves a contact by its email.

        :param limit: int: Limit the number of contacts returned
        :param offset: int: Determine how many records to skip
        :param contact_email: str: The email of the contact to search for
        :param db: AsyncSession, optional: The asynchronous database session used to query the database
               Defaults to `Depends(get_db)` to automatically manage the session
        :param user: User: Get the current authenticated user
        :return: Contact | None: The `Contact` object if a match is found, otherwise `None`
    """

    stmt = (
        select(Contact)
        .filter(Contact.user == user, Contact.email == contact_email)
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    return contact


async def get_upcoming_birthdays(db: AsyncSession, user: User):
    """
    The get_upcoming_birthdays function retrieves contacts with upcoming birthdays within the next 7 days from today.

        :param db: AsyncSession, optional: The asynchronous database session used to query the database
               Defaults to `Depends(get_db)` to automatically manage the session
        :param user: User: Get the current authenticated user
        :return: List[Contact]: A list of `Contact` objects whose birthdays are in the upcoming 7 days
    """

    current_date = date.today()
    future_date = current_date + timedelta(days=7)
    stmt = select(Contact).filter(
        current_date >= Contact.birthday, Contact.birthday <= future_date
    )
    result = await db.execute(stmt)
    contacts = result.scalars().all()
    return contacts


async def get_upcoming_birthdays_from_new_date(
    new_date: str, limit: int, offset: int, db: AsyncSession, user: User
) -> List[Contact]:
    """
    The get_upcoming_birthdays_from_new_date function retrieves contacts with upcoming birthdays within the next 7 days from new date.

        :param db: AsyncSession, optional: The asynchronous database session used to query the database
               Defaults to `Depends(get_db)` to automatically manage the session
        :param user: User: Get the current authenticated user
        :return:List[Contact]: A list of `Contact` objects whose birthdays are in the upcoming 7 days from new date
    """

    new_date_obj = datetime.strptime(new_date, "%Y-%m-%d").date()
    future_date = new_date_obj + timedelta(days=7)
    stmt = (
        select(Contact)
        .filter(Contact.birthday >= new_date_obj, Contact.birthday <= future_date)
        .limit(limit)
        .offset(offset)
    )
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def update_contact(
    body: ContactSchema,
    contact_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    """
    The update_contact function updates a contact's details using contact's ID (such as fullname, email, phone number, and birthday)
    for a specific user, ensuring that the user owns the contact.

    :param body: ContactSchema: The data used to update the contact (including fullname, email, phone number, and birthday).
    :param contact_id: int: The ID of the contact to be updated (must be greater than or equal to 1).
    :param db: AsyncSession: The database session used to execute the query.
    :param user: User: The current authenticated user who is attempting to update the contact.

    :return: Contact: The updated contact object after the changes have been applied.

    :raise: HTTPException: If the contact is not found for the specified user, a 404 error is raised.
    """

    stmt = select(Contact).filter(Contact.user == user, Contact.id == contact_id)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    contact.fullname = body.fullname
    contact.email = body.email
    contact.phone_number = body.phone_number
    contact.birthday = body.birthday

    await db.commit()
    await db.refresh(contact)
    return contact


async def delete_contact(
    contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db)
):
    """
    The delete_contact function deletes a contact using contact's ID.

    :param body: ContactSchema: The data used to update the contact (including fullname, email, phone number, and birthday).
    :param contact_id: int: The ID of the contact to be updated (must be greater than or equal to 1).
    :param db: AsyncSession: The database session used to execute the query.

    :return: Contact: The information about succefull deleting of the contact.

    :raise: HTTPException: If the contact is not found raises a 404 error.
    """

    stmt = select(Contact).filter(Contact.id == contact_id)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    await db.delete(contact)
    await db.commit()
    return {"detail": "Contact deleted successfully"}
