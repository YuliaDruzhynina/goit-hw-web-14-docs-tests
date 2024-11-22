# python -m unittest tests.test_repository_users
import unittest
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.schemas import UserModel
from src.repository.users import (
    get_user_by_email,
    create_user,
    update_token,
    confirmed_email,
    update_avatar_url
)


class TestContactFunctions(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = AsyncMock(spec=AsyncSession)
        self.user = User(
            id=1,
            email="old_email",
            refresh_token="old_token",
            confirmed=False,
            avatar="old_url",
        )
        self.user_data = {
            "id": 1,
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "password123",
            "refresh_token": "new_token",
        }

    async def test_get_user_by_email_found(self):

        user = User(
            id=self.user_data["id"],
            username=self.user_data["username"],
            email=self.user_data["email"],
            password=self.user_data["password"],
        )

        mock_result = AsyncMock()

        # Mock the scalar_one_or_none method to return the user object
        mock_result.scalar_one_or_none.return_value = user

        # Mock the execute method to return our mock_result
        self.session.execute.return_value = mock_result

        # Call the function with the mocked session
        result = await get_user_by_email(self.user_data["email"], db=self.session)

        # Assert that the correct user is returned and the email matches
        self.assertEqual(result.email, self.user_data["email"])

        # Assert that the execute method was called once
        self.session.execute.assert_called_once()

    async def test_get_user_by_email_not_found(self):
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        self.session.execute.return_value = mock_result
        result = await get_user_by_email(self.user_data["email"], db=self.session)

        self.assertIsNone(result)
        self.session.execute.assert_called_once()

    async def test_create_user(self):
        body = UserModel(
            username="Bob",
            email="test@example.com",
            password="123456789",
        )
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = User(
            username="Bob", email="test@example.com", password="123456789"
        )
        self.session.execute.return_value = mock_result
        result = await create_user(body, self.session)

        self.assertIsInstance(result, User)

    async def test_update_token(self):
        token = "new_tocken"
        await update_token(self.user, token, self.session)
        self.assertEqual(self.user.refresh_token, token)
        self.session.commit.assert_awaited_once()

    # test def confirmed_email with patch() for def get_user_by_email
    async def test_confirmed_email_success(self):
        email = self.user.email

        # Mock the get_user_by_email function in the test to return a user using patch
        with patch(
            "src.repository.users.get_user_by_email", return_value=self.user
        ) as mock_get_user_by_email:
            await confirmed_email(email, self.session)

            # check confurmed status
            self.assertTrue(self.user.confirmed)
            self.session.commit.assert_awaited_once()

            # check the function get_user_by_email was called with right email
            mock_get_user_by_email.assert_called_once_with(email, self.session)

    async def test_confirmed_email_user_not_found(self):
        incorrect_email = "nonexistent@example.com"

        # Mock the get_user_by_email function in the test to return None using patch
        with patch(
            "src.repository.users.get_user_by_email", return_value=None
        ) as mock_get_user_by_email:
            
            # Calling the function to confirm the email for a non-existent user
            with self.assertRaises(ValueError):
                
            # check ValueError for invalid email adress
                await confirmed_email(incorrect_email, self.session)

            # Check that commit was not called since the user was not found
            self.session.commit.assert_not_awaited()

            # Check that commit was not called since the user was not found 
            mock_get_user_by_email.assert_called_once_with(
                incorrect_email, self.session
            )

    # test def update_avatar_url with decorator @patch() for def get_user_by_email
    @patch("src.repository.users.get_user_by_email")
    async def test_update_avatar_url_success(self, mock_get_user_by_email):
        new_avatar_url = "new_avatar_url"

        # Mocking the behavior of get_user_by_email to return a mock user
        mock_get_user_by_email.return_value = self.user

        # Call the update_avatar_url function
        updated_user = await update_avatar_url(
            self.user.email, new_avatar_url, self.session
        )
        # Assert that get_user_by_email was called with the correct email
        mock_get_user_by_email.assert_called_once_with(self.user.email, self.session)

        # Assert that the avatar URL was updated
        self.assertEqual(updated_user.avatar, new_avatar_url)

        # Ensure that commit and refresh were called on the mock session
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(updated_user)

    @patch("src.repository.users.get_user_by_email")
    async def test_update_avatar_url_user_not_found(self, mock_get_user_by_email):
        new_avatar_url = "new_avatar_url"
        # Mocking the behavior of get_user_by_email to return a mock user
        mock_get_user_by_email.return_value = None
        with self.assertRaises(ValueError, msg="User not found"):
            await update_avatar_url(self.user.email, new_avatar_url, self.session)

        self.session.commit.assert_not_awaited()
        self.session.refresh.assert_not_awaited()
        mock_get_user_by_email.assert_called_once_with(self.user.email, self.session)
