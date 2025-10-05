"""
Валидаторы для бота типографии.
"""

import re
from dateparser import parse as dp


def to_int(s):
    """Преобразует строку в число."""
    s = s.strip().replace(" ", "")
    return int(s) if s.isdigit() else None


def is_multiple_of_50(n):
    """Проверяет, что число кратно 50 и больше или равно 50."""
    return n >= 50 and n % 50 == 0


# Размеры буклетов
FLY_SIZES = {
    "A7": (105, 74),
    "A6": (105, 148), 
    "A5": (210, 148),
    "A4": (210, 297)
}


def parse_fly_choice(text):
    """Парсит выбор формата буклета."""
    t = text.lower().replace("x", "×").replace("*", "×").replace("х", "×")
    for k, (w, h) in FLY_SIZES.items():
        if t.startswith(k.lower()) or t.startswith(f"{w}×{h}"):
            return k, (w, h)
    return None


def normalize_phone(s):
    """Нормализует номер телефона к формату +7XXXXXXXXXX."""
    digits = re.sub(r"\D", "", s)
    if digits.startswith("8") and len(digits) == 11:
        return "+7" + digits[1:]
    if digits.startswith("7") and len(digits) == 11:
        return "+7" + digits[1:]
    if len(digits) == 10 and digits[0] == "9":
        return "+7" + digits
    if s.strip().startswith("+7") and len(digits) == 11:
        return "+7" + digits[1:]
    return None


def parse_due(text, tz):
    """Парсит дату и время дедлайна."""
    dt = dp(
        text, 
        languages=["ru", "en"], 
        settings={
            "PREFER_DATES_FROM": "future",
            "TIMEZONE": tz,
            "RETURN_AS_TIMEZONE_AWARE": True
        }
    )
    return dt


def parse_custom_size(text: str) -> tuple[int, int] | None:
    """Парсит пользовательский размер в формате Ш×В мм."""
    if not text:
        return None
    
    # Нормализуем разделители
    text = text.strip().replace(" ", "").replace("x", "×").replace("X", "×").replace("*", "×")
    
    # Ищем паттерн Ш×В
    match = re.match(r"^(\d+)[×xX*](\d+)$", text)
    if not match:
        return None
    
    try:
        width = int(match.group(1))
        height = int(match.group(2))
        
        # Проверяем диапазон
        if not (20 <= width <= 1200 and 20 <= height <= 1200):
            return None
            
        return (width, height)
    except (ValueError, IndexError):
        return None


def parse_custom_size_mm(text: str) -> str | None:
    """Парсит пользовательский размер в мм и возвращает строку формата."""
    result = parse_custom_size(text)
    if result:
        width, height = result
        return f"{width}×{height} мм"
    return None


def parse_banner_size_m(text: str) -> str | None:
    """Парсит размер баннера в метрах и возвращает строку формата."""
    result = parse_banner_size(text)
    if result:
        width, height = result
        return f"{width}×{height} м"
    return None


def parse_bigovka_count(text: str) -> int | None:
    """Парсит количество линий биговки (0-5)."""
    if not text:
        return None
    
    try:
        count = int(text.strip())
        if 0 <= count <= 5:
            return count
        return None
    except ValueError:
        return None


def parse_banner_size(text: str) -> tuple[float, float] | None:
    """Парсит размер баннера в метрах."""
    if not text:
        return None
    
    # Нормализуем разделители
    text = text.strip().replace(" ", "").replace("x", "×").replace("X", "×").replace("*", "×")
    
    # Ищем паттерн Ш×В
    match = re.match(r"^(\d+(?:\.\d+)?)[×xX*](\d+(?:\.\d+)?)$", text)
    if not match:
        return None
    
    try:
        width = float(match.group(1))
        height = float(match.group(2))
        
        # Проверяем диапазон (0.1-20.0 метров)
        if not (0.1 <= width <= 20.0 and 0.1 <= height <= 20.0):
            return None
            
        return (width, height)
    except (ValueError, IndexError):
        return None