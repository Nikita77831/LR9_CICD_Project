"""Шаги для BDD-тестирования behave."""
import os
import sys
import tempfile
from behave import given, when, then

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from auth_module import AuthenticationService, UserUpdater

def setup_fresh_context(context):
    """Изоляция каждого сценария во временных файлах."""
    context.temp_auth = tempfile.NamedTemporaryFile(
        mode='w', suffix='.json', delete=False, encoding='utf-8')
    context.temp_auth.write('[]')
    context.temp_auth.close()
    context.temp_csv = tempfile.NamedTemporaryFile(
        mode='w', suffix='.csv', delete=False, encoding='utf-8')
    context.temp_csv.write("date,value\n2024-01-01,100\n2024-01-02,110\n2024-01-03,120\n")
    context.temp_csv.close()
    context.auth = AuthenticationService(context.temp_auth.name)
    context.updater = UserUpdater(context.auth, context.temp_csv.name)
    context.result = None

@given('система инициализирована с пустым хранилищем пользователей')
def step_init_empty(context):
    setup_fresh_context(context)

@given('создан временный CSV-файл с данными прогноза')
def step_csv_ready(context):
    pass

@given('зарегистрированы пользователи "{admin_user}" ("{admin_pass}") '
       'и "{target_user}" ("{target_pass}")')
def step_reg_two(context, admin_user, admin_pass, target_user, target_pass):
    setup_fresh_context(context)
    context.auth.register_user(admin_user, admin_pass, "admin")
    context.auth.register_user(target_user, target_pass, "viewer")

@given('система готова к регистрации')
def step_ready_reg(context):
    setup_fresh_context(context)

@when('я обновляю данные пользователя "{username}" с паролем "{password}"')
def step_update_user(context, username, password):
    context.result = context.updater.update(username, password)

@when('администратор меняет роль пользователя "{target}" на "{new_role}"')
def step_change_role(context, target, new_role):
    admin = context.auth.login("admin", "AdminPass1!")
    target_user = next((u for u in context.auth.users.values()
                        if u.username == target), None)
    if admin and target_user:
        success = context.auth.change_user_role(admin, target_user.id, new_role)
        context.result = {"success": success, "user": target_user}
    else:
        context.result = {"success": False, "message": "Auth or user not found"}

@when('я пытаюсь зарегистрировать пользователя с паролем "{password}"')
def step_try_reg_impl(context, password):
    context.result = context.auth.register_user("test_user", password, "viewer")

@then('операция должна завершиться успешно')
def step_verify_success(context):
    assert context.result["success"] is True, f"Expected success, got: {context.result}"

@then('пользователь должен получить роль "{role}" по умолчанию')
def step_verify_role(context, role):
    assert context.result["user"]["role"] == role

@then('внешний источник данных должен быть помечен как "{status}"')
def step_verify_data_source(context, status):
    assert context.result.get("data_source") == status

@then('операция должна вернуть статус неудачи')
def step_verify_fail(context):
    assert context.result["success"] is False

@then('сообщение должно содержать "{msg}"')
def step_verify_msg(context, msg):
    assert msg in context.result.get("message", "")

@then('роль пользователя "{username}" должна измениться на "{new_role}"')
def step_verify_role_change(context, username, new_role):
    found = any(u.username == username and u.role == new_role
                for u in context.auth.users.values())
    assert found, f"User {username} role is not {new_role}"

@then('результат регистрации должен быть {is_success}')
def step_check_reg(context, is_success):
    expected = is_success == "True"
    if expected:
        assert context.result is not None, "Registration should succeed"
    else:
        assert context.result is None, "Registration should fail"

def after_scenario(context, scenario):
    """Очистка временных файлов после каждого сценария."""
    for attr in ['temp_auth', 'temp_csv']:
        if hasattr(context, attr) and os.path.exists(getattr(context, attr).name):
            try:
                os.remove(getattr(context, attr).name)
            except OSError:
                pass