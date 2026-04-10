"""Интеграционные тесты."""
import unittest
import os
import tempfile
from auth_module import AuthenticationService, UserUpdater
from forecast_module import TimeSeriesForecaster

class TestBigBang(unittest.TestCase):
    """Метод «Большого взрыва»."""
    def setUp(self):
        self.temp_auth = tempfile.NamedTemporaryFile(
            delete=False, suffix='.json')
        self.temp_auth.close()
        self.temp_data = tempfile.NamedTemporaryFile(
            mode='w', suffix='.csv', delete=False)
        self.temp_data.write("date,value\n2024-01-01,100\n2024-01-02,110\n")
        self.temp_data.close()
        self.auth = AuthenticationService(self.temp_auth.name)
        self.updater = UserUpdater(self.auth, self.temp_data.name)

    def tearDown(self):
        for f in [self.temp_auth.name, self.temp_data.name]:
            if os.path.exists(f):
                os.remove(f)

    def test_big_bang_full(self):
        result = self.updater.update("testuser", "TestPass123")
        self.assertTrue(result["success"])
        self.assertEqual(result["data_source"], "available")

    def test_big_bang_missing_file(self):
        broken = UserUpdater(self.auth, "/nonexistent.csv")
        result = broken.update("user2", "TestPass456")
        self.assertEqual(result["data_source"], "missing")

class TestBottomUp(unittest.TestCase):
    """Метод «Снизу вверх»."""
    def test_level_2_auth(self):
        temp = tempfile.NamedTemporaryFile(
            delete=False, suffix='.json')
        temp.close()
        auth = AuthenticationService(temp.name)
        self.assertIsNotNone(auth.register_user("u1", "Pass1234!", "viewer"))
        os.unlink(temp.name)