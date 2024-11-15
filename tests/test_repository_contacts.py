#PYTHONPATH=../src python -m unittest discover -s . -p "test_*.py"
import sys
import os
import unittest
from unittest.mock import MagicMock, AsyncMock
# from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.entity.models import Contact, User
from src.schemas import ContactSchema
from src.repository.contacts import (
    create_contact,
    # get_all_contacts,
    # get_contact_by_id,
    # get_contact_by_fullname,
    # get_contact_by_email,
    # get_upcoming_birthdays,
    # get_upcoming_birthdays_from_new_date,
    # update_contact,
    # delete_contact
)

#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


class TestContactFunctions(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=AsyncSession)
        self.user = User(id=1)

        self.contact_data = MagicMock(spec=ContactSchema)
        self.contact_data.fullname = "Bob Big"
        self.contact_data.email = "test@example.com"
        self.contact_data.phone_number = "+123456789"
        self.contact_data.birthday = "2000-02-02"

    async def test_create_contact_already_exists(self):
        mock_existing_contact = MagicMock(spec=Contact)
        self.session.execute.return_value.scalar_one_or_none = AsyncMock(return_value=mock_existing_contact)
        with self.assertRaises(HTTPException) as context:
            await create_contact(self.contact_data, self.session, self.user)
        
        self.assertEqual(context.exception.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(context.exception.detail, "Contact already exists!")

    async def test_create_contact_success(self):
        self.session.execute.return_value.scalar_one_or_none = AsyncMock(return_value=None)

        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()

        result = await create_contact(self.contact_data, self.session, self.user)
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once()

        self.assertIsInstance(result, Contact)
        self.assertEqual(result.fullname, "Bob Big")
        self.assertEqual(result.email, "test@example.com")


if __name__ == '__main__':
    unittest.main()