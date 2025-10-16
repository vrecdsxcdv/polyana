# services/validators.py
from __future__ import annotations

import datetime as dt
import re
from zoneinfo import ZoneInfo
import dateparser

RU_NUMS = {
    "один":1,"два":2,"три":3,"четыре":4,"пять":5,
    "шесть":6,"семь":7,"восемь":8,"девять":9,"десять":10,
}


def parse_due(text: str, tz: str):
    """
    Парсит срок. Возвращает TZ-aware datetime или None (если пропуск).
    Поддерживает:
      - "завтра 14:30", "сегодня 18:00", "через 2 часа"
      - "5.09", "05.10 16:00" (без времени -> 18:00)
      - "asap", "сейчас", "после проверки" -> None (как пропуск)
    Никогда не возвращает прошлое – сдвигает на следующий день.
    """
    if not text:
        return None
    txt = text.strip().lower()
    if txt in {"asap", "сейчас", "после проверки", "после проверки макета", "пропустить"}:
        return None

    tzinfo = ZoneInfo(tz)
    now = dt.datetime.now(tzinfo)

    # Формат "дд.мм" или "дд.мм чч:мм"
    m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})(?:\s+(\d{1,2})(?::(\d{2}))?)?", txt)
    if m:
        d, mth, hh, mm = m.groups()
        d = int(d); mth = int(mth)
        hh = int(hh) if hh is not None else 18
        mm = int(mm) if mm is not None else 0
        year = now.year
        try:
            cand = dt.datetime(year, mth, d, hh, mm, tzinfo=tzinfo)
            if cand < now:
                cand = dt.datetime(year + 1, mth, d, hh, mm, tzinfo=tzinfo)
            return cand
        except ValueError:
            return None

    settings = {
        "PREFER_DATES_FROM": "future",
        "TIMEZONE": tz,
        "RETURN_AS_TIMEZONE_AWARE": True,
        "DATE_ORDER": "DMY",
        "RELATIVE_BASE": now,
    }
    d = dateparser.parse(text, settings=settings, languages=["ru","en"])
    if not d:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=tzinfo)
    if d < now:
        d += dt.timedelta(days=1)
    return d


def validate_phone(phone: str) -> bool:
    """
    Проверяет российский номер телефона.
    Принимает форматы: +7XXXXXXXXXX, 8XXXXXXXXXX, 7XXXXXXXXXX
    """
    if not phone:
        return False
    
    # Убираем все символы кроме цифр и +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Проверяем паттерны
    patterns = [
        r'^\+7\d{10}$',  # +7XXXXXXXXXX
        r'^8\d{10}$',    # 8XXXXXXXXXX
        r'^7\d{10}$',    # 7XXXXXXXXXX
    ]
    
    for pattern in patterns:
        if re.match(pattern, cleaned):
            return True
    
    return False


def normalize_phone(phone: str) -> str:
    """
    Нормализует российский номер телефона к формату +7XXXXXXXXXX
    """
    if not phone:
        return ""
    
    # Убираем все символы кроме цифр и +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Нормализуем к +7XXXXXXXXXX
    if cleaned.startswith('+7') and len(cleaned) == 12:
        return cleaned
    elif cleaned.startswith('8') and len(cleaned) == 11:
        return '+7' + cleaned[1:]
    elif cleaned.startswith('7') and len(cleaned) == 11:
        return '+' + cleaned
    
    return phone  # Возвращаем как есть, если не удалось нормализовать


def validate_bc_quantity(qty: int) -> bool:
    """
    Проверяет количество визиток (кратно 50, минимум 50)
    """
    return qty >= 50 and qty % 50 == 0


def validate_quantity(qty: int) -> bool:
    """
    Проверяет обычное количество (положительное целое)
    """
    return qty > 0


def parse_exemplars(text: str) -> int | None:
    """
    Парсит количество экземпляров из текста.
    Поддерживает числа (3, 5) и русские слова (три, пять).
    """
    if not text: 
        return None
    t = text.strip().lower()
    # число цифрами
    m = re.search(r"\d+", t)
    if m:
        n = int(m.group())
        return n if n > 0 else None
    # число словами
    for w, n in RU_NUMS.items():
        if w in t:
            return n
    return None
