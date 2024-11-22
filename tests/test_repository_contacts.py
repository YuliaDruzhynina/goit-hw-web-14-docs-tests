# python -m unittest tests.test_repository_contacts
import unittest
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.entity.models import Contact, User
from src.schemas import ContactSchema
from src.repository.contacts import (
    create_contact,
    get_all_contacts,
    get_contact_by_id,
    get_contact_by_fullname,
    get_contact_by_email,
    get_upcoming_birthdays,
    update_contact,
    delete_contact,
)


class TestContactFunctions(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = AsyncMock(spec=AsyncSession)
        self.user = User(id=1)

        self.contact_data = MagicMock(spec=ContactSchema)
        self.contact_data.fullname = "Bob Big"
        self.contact_data.email = "test@example.com"
        self.contact_data.phone_number = "+123456789"
        self.contact_data.birthday = "2000-02-02"

    async def test_create_contact_already_exists(self):
        mock_existing_contact = MagicMock(spec=Contact)
        self.session.execute.return_value.scalar_one_or_none = AsyncMock(
            return_value=mock_existing_contact
        )
        with self.assertRaises(HTTPException) as context:
            await create_contact(self.contact_data, self.session, self.user)

        self.assertEqual(context.exception.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(context.exception.detail, "Contact already exists!")

    async def test_create_contact_success(self):
        self.session.execute.return_value.scalar_one_or_none = AsyncMock(
            return_value=None
        )

        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()

        result = await create_contact(self.contact_data, self.session, self.user)

        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once()

        self.assertIsInstance(result, Contact)
        self.assertEqual(result.fullname, "Bob Big")
        self.assertEqual(result.phone_number, "+123456789")
        self.assertEqual(result.email, "test@example.com")
        self.assertEqual(result.birthday, "2000-02-02")

    async def test_get_all_contacts_success(self):
        contacts = [
            Contact(
                id=1,
                fullname="Bob Big",
                email="test@example.com",
                birthday="2000-02-02",
            ),
            Contact(
                id=2,
                fullname="Boob Biig",
                email="test2@example.com",
                birthday="2002-02-02",
            ),
        ]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts

        result = await get_all_contacts(limit=10, offset=0, db=self.session)

        self.assertEqual(result, contacts)
        self.session.execute.assert_called_once()

    async def test_get_contact_by_id_found(self):
        # Set up the mock to return a specific contact by ID
        contact_id = 1
        self.session.execute.return_value.scalar_one_or_none.return_value = contact_id

        # Call the function with the mocked session
        result = await get_contact_by_id(
            limit=1, offset=0, contact_id=contact_id, db=self.session
        )

        # Assert that the correct contact was returned
        self.assertEqual(result, contact_id)
        self.session.execute.assert_called_once()

    async def test_get_contact_by_id_not_found(self):
        # Set up the mock to return None (contact not found)
        contact_id = 1
        self.session.execute.return_value.scalar_one_or_none.return_value = None

        # Call the function and assert that an HTTPException is raised
        with self.assertRaises(HTTPException) as context:
            await get_contact_by_id(
                limit=1, offset=0, contact_id=contact_id, db=self.session
            )

        # Check that the exception status code is 404 and message is "NOT FOUND"
        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(context.exception.detail, "NOT FOUND")

    async def test_get_contact_by_fullname(self):
        contact_fullname = "Bob Big"
        contact = Contact(
            id=1,
            fullname=contact_fullname,
            email="test@example.com",
            phone_number="+123456789",
            birthday="2000-02-02",
        )

        self.session.execute.return_value.scalar_one_or_none.return_value = contact
        result = await get_contact_by_fullname(
            limit=1,
            offset=0,
            contact_fullname=contact_fullname,
            db=self.session,
            user=self.user,
        )
        self.assertEqual(result, contact)

    async def test_get_contact_by_email(self):
        contact_email = "test@example.com"
        contact = Contact(
            id=1,
            fullname="Bob Big",
            email=contact_email,
            phone_number="+123456789",
            birthday="2000-02-02",
        )

        self.session.execute.return_value.scalar_one_or_none.return_value = contact
        result = await get_contact_by_email(
            limit=1,
            offset=0,
            contact_email=contact_email,
            db=self.session,
            user=self.user,
        )
        self.assertEqual(result, contact)

    async def test_get_upcoming_birthdays(self):
        contacts = [
            Contact(
                id=1,
                fullname="Bob Big",
                email="test@example.com",
                birthday="2000-02-02",
            ),
            Contact(
                id=2,
                fullname="Boob Biig",
                email="test2@example.com",
                birthday="2002-02-02",
            ),
        ]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await get_upcoming_birthdays(db=self.session, user=self.user)

        self.assertEqual(result, contacts)
        # self.session.execute.assert_called_once()

    async def test_update_contact_success(self):

        body = ContactSchema(
            fullname="Bob Big",
            email="test@example.com",
            phone_number="+123456789",
            birthday="2000-02-02",
        )
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = Contact(
            id=1,
            fullname="old_name",
            email="old@example.com",
            phone_number="+111156789",
            birthday="2000-01-01",
        )
        self.session.execute.return_value = mocked_contact

        result = await update_contact(body, 1, self.session, self.user)

        self.assertIsInstance(result, Contact)

    async def test_delete_contact(self):
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = Contact(
            id=1,
            fullname="old_name",
            email="old@example.com",
            phone_number="+111156789",
            birthday="2000-01-01",
        )
        self.session.execute.return_value = mocked_contact

        result = await delete_contact(1, self.session)

        self.session.delete.assert_called_once
        self.session.commit.assert_called_once
        self.assertEqual(result, {"detail": "Contact deleted successfully"})


if __name__ == "__main__":
    unittest.main()  # Ensure tests are discovered and run
