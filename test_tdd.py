# test_tdd.py
"""TDD тесты для проверки силы пароля."""
import pytest
from pages import AuthPage

@pytest.fixture
def auth_page():
    return AuthPage()

def test_tdd_red_1_short_password(auth_page):
    assert auth_page.is_password_strong("short") is False

def test_tdd_red_2_no_digit(auth_page):
    assert auth_page.is_password_strong("abcdefgh") is False

def test_tdd_red_3_empty_or_none(auth_page):
    assert auth_page.is_password_strong("") is False
    assert auth_page.is_password_strong(None) is False

def test_tdd_green_valid_password(auth_page):
    assert auth_page.is_password_strong("StrongPass1") is True
    assert auth_page.is_password_strong("Pass1234") is True