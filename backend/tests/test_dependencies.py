"""Focused authentication tests that do not require a Supabase project."""
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, patch

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.dependencies import get_current_user


class FakeProfileQuery:
    def select(self, *_args):
        return self

    def eq(self, *_args):
        return self

    def maybe_single(self):
        return self

    def execute(self):
        return SimpleNamespace(data={"is_admin": True})


class AuthenticationDependencyTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="valid-token"
        )

    async def test_uses_supabase_to_validate_the_access_token(self):
        client = Mock()
        client.auth.get_user.return_value = SimpleNamespace(
            user=SimpleNamespace(id="user-123", email="admin@example.com")
        )
        client.table.return_value = FakeProfileQuery()

        with patch("app.dependencies.get_supabase_client", return_value=client):
            user = await get_current_user(self.credentials)

        client.auth.get_user.assert_called_once_with("valid-token")
        self.assertEqual(user.id, "user-123")
        self.assertEqual(user.email, "admin@example.com")
        self.assertTrue(user.is_admin)

    async def test_rejects_an_invalid_access_token(self):
        client = Mock()
        client.auth.get_user.side_effect = RuntimeError("token rejected")

        with patch("app.dependencies.get_supabase_client", return_value=client):
            with self.assertRaises(HTTPException) as raised:
                await get_current_user(self.credentials)

        self.assertEqual(raised.exception.status_code, 401)
        self.assertEqual(raised.exception.detail, "Invalid or expired access token")
