"""Тесты модуля авторизации."""
import unittest
import os
import tempfile
from auth_module import User, AuthenticationService

class TestUser(unittest.TestCase):
    """Тесты для класса User."""
    def setUp(self):
        self.user = User(1, "testuser", "TestPass123", "analyst")

    def test_password_hashing(self):
        self.assertNotEqual(self.user.password_hash, "TestPass123")
        self.assertEqual(len(self.user.password_hash), 64)

    def test_password_validation(self):
        self.assertFalse(self.user.validate_password("Short1"))
        self.assertTrue(self.user.validate_password("ValidPass123"))

    def test_change_password(self):
        old_hash = self.user.password_hash
        self.assertFalse(self.user.change_password("WrongPass123", "NewPass123"))
        self.assertTrue(self.user.change_password("TestPass123", "NewPass123"))
        self.assertNotEqual(self.user.password_hash, old_hash)

class TestAuthenticationService(unittest.TestCase):
    """Тесты для AuthenticationService."""
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix='.json')
        self.temp_file.close()
        self.auth_service = AuthenticationService(self.temp_file.name)
        self.admin = self.auth_service.register_user(
            "admin", "AdminPass123", "admin")

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_user_registration(self):
        user = self.auth_service.register_user(
            "newuser", "UserPass123", "analyst")
        self.assertIsNotNone(user)
        self.assertIsNone(self.auth_service.register_user(
            "newuser", "AnotherPass123"))

    def test_login(self):
        self.auth_service.register_user("testuser", "TestPass123", "viewer")
        self.assertIsNotNone(
            self.auth_service.login("testuser", "TestPass123"))
        self.assertIsNone(self.auth_service.login("testuser", "WrongPass"))

    def test_change_user_role(self):
        user = self.auth_service.register_user(
            "regular", "RegularPass123", "viewer")
        self.assertTrue(self.auth_service.change_user_role(
            self.admin, user.id, "analyst"))

    def test_access_control(self):
        viewer = self.auth_service.register_user(
            "v1", "ViewerPass123", "viewer")
        self.assertTrue(self.auth_service.check_access(viewer, "viewer"))
        self.assertFalse(self.auth_service.check_access(viewer, "admin"))