import pytest
from typing import List

def check_email(email: str) -> bool:
    return '@' in email and '.' in email and ' ' not in email

def fio(initials: List[str]) -> str:
    surname, name, fam = initials
    return ''.join([surname[0], name[0], fam[0]])

def list_of_numbers(n: int) -> list:
    return list(range(1, n + 1))

# === ТЕСТЫ ===

@pytest.mark.parametrize("email, expected", [
    ("test@example.com", True),
    ("user.name@domain.org", True),
    ("a@b.c", True),
    ("testexample.com", False),      # нет @
    ("test@examplecom", False),      # нет .
    ("test @example.com", False),    # есть пробел
    ("", False),                     # пустая строка
])
def test_check_email(email, expected):
    assert check_email(email) == expected

@pytest.mark.parametrize("initials, expected", [
    (["Иванов", "Иван", "Иванович"], "ИИИ"),
    (["Сидоров", "Алексей", "Петрович"], "САП"),
    (["Пушкин", "Александр", "Сергеевич"], "ПАС"),
])
def test_fio(initials, expected):
    assert fio(initials) == expected

@pytest.mark.parametrize("n, expected", [
    (5, [1, 2, 3, 4, 5]),
    (1, [1]),
    (0, []),
    (3, [1, 2, 3]),
])
def test_list_of_numbers(n, expected):
    assert list_of_numbers(n) == expected