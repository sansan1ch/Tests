import pytest
import requests
import os
import uuid
from urllib.parse import quote

BASE_URL = "https://cloud-api.yandex.net/v1/disk/resources"
YANDEX_TOKEN = os.getenv("YANDEX_DISK_TOKEN", "ваш!!!!!")


def get_headers(token=YANDEX_TOKEN):
    return {"Authorization": f"OAuth {token}"}


def safe_delete(path):
    """Гарантированно удаляет папку, игнорируя ошибки."""
    try:
        if YANDEX_TOKEN and YANDEX_TOKEN != "ваш!!!!!":
            encoded_path = quote(path, safe="/")
            requests.delete(f"{BASE_URL}?path={encoded_path}", headers=get_headers(), timeout=10)
    except Exception:
        pass  # Игнорируем ошибки в teardown


@pytest.fixture
def clean_folder():
    folder_name = f"pytest_{uuid.uuid4().hex[:6]}"
    folder_path = f"/{folder_name}"
    safe_delete(folder_path)
    yield folder_path
    safe_delete(folder_path)


# Положительный тест
def test_create_folder_success(clean_folder):
    response = requests.put(
        f"{BASE_URL}?path={clean_folder}",
        headers=get_headers(),
        timeout=10
    )
    assert response.status_code in (200, 201), (
        f"Ожидался 200/201, получен {response.status_code}\nОтвет: {response.text}"
    )
    # Проверяем, что папка реально создана
    check = requests.get(
        f"{BASE_URL}?path={clean_folder}",
        headers=get_headers(),
        timeout=10
    )
    assert check.status_code == 200
    assert check.json().get("type") == "dir", "Созданный ресурс должен быть директорией"


# Отрицательные тесты — с учётом РЕАЛЬНОГО поведения API Яндекс.Диска
AUTH_HEADER = get_headers()


@pytest.mark.parametrize("path, headers, expected_status, description, setup_action", [
    # === 401: Авторизация ===
    ("/test_token", {"Authorization": "OAuth invalid_token"}, 401, "Невалидный токен", None),
    ("/test_no_auth", {}, 401, "Нет заголовка авторизации", None),
    ("/nonexistent_abc123/new_folder", AUTH_HEADER, 409, "Родительская папка не найдена", None),

    # === 409: Папка уже существует ===
    ("/pytest_dup_test", AUTH_HEADER, 409, "Папка уже существует", "create_first"),
])
def test_create_folder_negative(path, headers, expected_status, description, setup_action):
    # Предварительное действие: создаём папку для теста на дублирование
    if setup_action == "create_first":
        safe_delete(path)  # На всякий случай чистим перед тестом
        requests.put(f"{BASE_URL}?path={path}", headers=AUTH_HEADER, timeout=10)

    encoded_path = quote(path, safe="/")
    url = f"{BASE_URL}?path={encoded_path}"

    response = requests.put(url, headers=headers, timeout=10)

    assert response.status_code == expected_status, (
        f"Тест '{description}' не прошёл.\n"
        f"URL: {url}\n"
        f"Ожидался: {expected_status}, получен: {response.status_code}\n"
        f"Ответ API: {response.text}"
    )

    # Дополнительная проверка: для 409 убеждаемся, что в ответе есть информация об ошибке
    if expected_status == 409:
        try:
            error_data = response.json()
            assert "error" in error_data, "В ответе 409 должно быть поле 'error'"
        except ValueError:
            pass  # Если ответ не JSON, просто пропускаем дополнительную проверку