"""Модуль авторизации и управления пользователями."""
import hashlib
import json
import os
from datetime import datetime
from typing import Optional, Dict

class User:
    """Класс пользователя системы."""
    def __init__(self, user_id: int, username: str, password: str, role: str):
        self.id = user_id
        self.username = username
        self.password_hash = self._hash_password(password)
        self.role = role
        self.created_at = datetime.now()
        self.last_login = None

    def _hash_password(self, password: str) -> str:
        """Хеширование пароля."""
        salt = "production_forecast_salt"
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def validate_password(self, password: str) -> bool:
        """Проверка сложности пароля."""
        if len(password) < 8:
            return False
        if not any(c.isupper() for c in password):
            return False
        if not any(c.isdigit() for c in password):
            return False
        return True

    def change_password(self, old_password: str, new_password: str) -> bool:
        """Смена пароля."""
        if not self.validate_password(new_password):
            return False
        old_hash = self._hash_password(old_password)
        if old_hash != self.password_hash:
            return False
        self.password_hash = self._hash_password(new_password)
        return True

    def to_dict(self) -> Dict:
        """Сериализация в словарь."""
        return {
            'id': self.id,
            'username': self.username,
            'password_hash': self.password_hash,
            'role': self.role,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class AuthenticationService:
    """Сервис аутентификации."""
    def __init__(self, storage_file: str = "users.json"):
        self.storage_file = storage_file
        self.users: Dict[int, User] = {}
        self.current_user: Optional[User] = None
        self._load_users()

    def _load_users(self) -> None:
        """Загрузка пользователей из файла."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_data in data:
                        user = User(
                            user_data['id'], user_data['username'],
                            "dummy", user_data['role']
                        )
                        user.password_hash = user_data['password_hash']
                        self.users[user.id] = user
            except (json.JSONDecodeError, IOError, KeyError) as e:
                print(f"Warning: Failed to load users.json: {e}")
                self.users = {}

    def _save_users(self) -> None:
        """Сохранение пользователей в файл."""
        data = [user.to_dict() for user in self.users.values()]
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def register_user(self, username: str, password: str,
                      role: str = "viewer") -> Optional[User]:
        """Регистрация нового пользователя."""
        for user in self.users.values():
            if user.username == username:
                return None
        temp_user = User(0, username, password, role)
        if not temp_user.validate_password(password):
            return None
        new_id = max(self.users.keys()) + 1 if self.users else 1
        new_user = User(new_id, username, password, role)
        self.users[new_id] = new_user
        self._save_users()
        return new_user

    def login(self, username: str, password: str) -> Optional[User]:
        """Вход пользователя в систему."""
        for user in self.users.values():
            if user.username == username:
                if user._hash_password(password) == user.password_hash:
                    user.last_login = datetime.now()
                    self.current_user = user
                    self._save_users()
                    return user
        return None

    def change_user_role(self, admin_user: User, target_user_id: int,
                         new_role: str) -> bool:
        """Изменение роли пользователя."""
        if admin_user.role != "admin":
            return False
        if new_role not in ["admin", "analyst", "viewer"]:
            return False
        if target_user_id not in self.users:
            return False
        self.users[target_user_id].role = new_role
        self._save_users()
        return True

    def check_access(self, user: User, required_role: str) -> bool:
        """Проверка прав доступа."""
        roles_level = {"viewer": 1, "analyst": 2, "admin": 3}
        return roles_level.get(user.role, 0) >= roles_level.get(required_role, 0)

    def is_password_strong(self, password: str) -> bool:
        """Проверка силы пароля для TDD."""
        if not password or not isinstance(password, str):
            return False
        if len(password) < 8:
            return False
        return any(char.isdigit() for char in password)

class UserUpdater:
    """Обновление пользователя и проверка источников данных."""
    def __init__(self, auth_service: AuthenticationService,
                 data_source_path: str):
        self.auth = auth_service
        self.data_source_path = data_source_path

    def _handle_password_update(self, user: User, old_pass: str,
                                new_pass: str, result: Dict) -> None:
        if new_pass and user.validate_password(new_pass):
            if user.change_password(old_pass, new_pass):
                result["message"] += ", password updated"

    def _handle_role_update(self, user: User, new_role: str, result: Dict) -> None:
        if new_role and self.auth.current_user:
            if self.auth.current_user.role == "admin":
                if self.auth.change_user_role(self.auth.current_user, user.id, new_role):
                    result["message"] += ", role updated"

    def update(self, username: str, password: str,
               new_role: Optional[str] = None,
               new_password: Optional[str] = None) -> Dict:
        """Основной метод обновления/регистрации пользователя."""
        result = {"success": False, "message": "", "user": None}

        user = self.auth.login(username, password)
        if user is None:
            user = self.auth.register_user(username, password, "viewer")
            if user is None:
                result["message"] = "Registration failed"
                return result
            result["message"] = "User registered"
        else:
            result["message"] = "User logged in"

        self._handle_password_update(user, password, new_password, result)
        self._handle_role_update(user, new_role, result)

        if os.path.exists(self.data_source_path):
            result["data_source"] = "available"
        else:
            result["data_source"] = "missing"

        result["success"] = True
        result["user"] = user.to_dict()
        self.auth._save_users()
        return result