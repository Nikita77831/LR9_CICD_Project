"""Page Object для операций авторизации."""
import os
import tempfile
from typing import Optional, Dict
from auth_module import AuthenticationService

class AuthPage:
    """Обертка для UI-сценариев авторизации."""
    def __init__(self, users_file: Optional[str] = None):
        self._temp_file = None
        if users_file is None:
            self._temp_file = tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False, encoding='utf-8')
            self._temp_file.write('[]')
            self._temp_file.close()
            self.users_file = self._temp_file.name
        else:
            self.users_file = users_file
        self.auth = AuthenticationService(self.users_file)
        self.last_error: Optional[str] = None

    def __del__(self):
        """Очистка временного файла."""
        if self._temp_file and os.path.exists(self.users_file):
            try:
                os.remove(self.users_file)
            except OSError:
                pass

    def register(self, username: str, password: str,
                 role: str = "viewer") -> Dict:
        """Сценарий регистрации."""
        result = self.auth.register_user(username, password, role)
        if result:
            return {"success": True, "user": result.to_dict(),
                    "message": "Registered"}
        self.last_error = "Registration failed (user exists or weak pwd)"
        return {"success": False, "error": self.last_error}

    def login(self, username: str, password: str) -> Dict:
        """Сценарий входа."""
        result = self.auth.login(username, password)
        if result:
            return {"success": True, "user": result.to_dict(),
                    "message": "Logged in"}
        self.last_error = "Invalid credentials"
        return {"success": False, "error": self.last_error}

    def change_role(self, admin_username: str, admin_password: str,
                    target_username: str, new_role: str) -> Dict:
        """Сценарий смены роли админом."""
        admin = self.auth.login(admin_username, admin_password)
        if not admin or admin.role != "admin":
            return {"success": False, "error": "Admin auth failed"}
        target_user = next(
            (u for u in self.auth.users.values()
             if u.username == target_username), None)
        if not target_user:
            return {"success": False, "error": "Target user not found"}
        success = self.auth.change_user_role(admin, target_user.id, new_role)
        return {"success": True, "message": f"Role changed to {new_role}"} \
            if success else {"success": False, "error": "Role change failed"}

    def get_user(self, username: str) -> Optional[Dict]:
        """Получить данные пользователя."""
        for user in self.auth.users.values():
            if user.username == username:
                return user.to_dict()
        return None

    def is_password_strong(self, password: str) -> bool:
        """Делегирование к методу TDD."""
        return self.auth.is_password_strong(password)