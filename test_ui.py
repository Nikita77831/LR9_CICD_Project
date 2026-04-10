# test_ui.py
"""UI-сценарии через Page Object."""
import pytest
from pages import AuthPage

@pytest.fixture
def auth_page():
    page = AuthPage()
    yield page

def test_ui_scenario_1_successful_login(auth_page):
    reg_result = auth_page.register("testuser", "TestPass123", "viewer")
    assert reg_result["success"] is True
    login_result = auth_page.login("testuser", "TestPass123")
    assert login_result["success"] is True

def test_ui_scenario_2_wrong_password(auth_page):
    auth_page.register("admin", "CorrectPass1!", "admin")
    login_result = auth_page.login("admin", "WrongPassword999")
    assert login_result["success"] is False

def test_ui_scenario_3_register_and_change_role(auth_page):
    auth_page.register("admin", "AdminPass123!", "admin")
    auth_page.register("analyst1", "AnalystPass1!", "viewer")
    role_result = auth_page.change_role(
        "admin", "AdminPass123!", "analyst1", "analyst")
    assert role_result["success"] is True
    assert auth_page.get_user("analyst1")["role"] == "analyst"