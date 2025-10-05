"""
Тесты для сервиса парсинга.
"""

import pytest
from datetime import datetime
from services.parsing import ParsingService


class TestParsingService:
    """Тесты для ParsingService."""
    
    def test_parse_quantity_valid(self):
        """Тест парсинга валидного количества."""
        assert ParsingService.parse_quantity("100") == 100
        assert ParsingService.parse_quantity("Тираж: 500 штук") == 500
        assert ParsingService.parse_quantity("Нужно 50 экземпляров") == 50
    
    def test_parse_quantity_invalid(self):
        """Тест парсинга невалидного количества."""
        assert ParsingService.parse_quantity("abc") is None
        assert ParsingService.parse_quantity("0") is None
        assert ParsingService.parse_quantity("1000000") is None  # Превышает лимит
        assert ParsingService.parse_quantity("") is None
    
    def test_parse_format_standard(self):
        """Тест парсинга стандартных форматов."""
        assert ParsingService.parse_format("A4") == "A4 (210×297 мм)"
        assert ParsingService.parse_format("a5") == "A5 (148×210 мм)"
        assert ParsingService.parse_format("A6 формат") == "A6 (105×148 мм)"
    
    def test_parse_format_custom(self):
        """Тест парсинга пользовательских размеров."""
        assert ParsingService.parse_format("210×297 мм") == "210×297 мм"
        assert ParsingService.parse_format("100 x 150 мм") == "100×150 мм"
        assert ParsingService.parse_format("Размер: 200×300") == "Размер: 200×300"  # Не парсится, возвращается как есть
    
    def test_parse_deadline_valid(self):
        """Тест парсинга валидных дат."""
        # Тест с конкретной датой (используем будущую дату)
        deadline = ParsingService.parse_deadline("05.10.2025 14:00")
        assert deadline is not None
        assert deadline.year == 2025
        assert deadline.month == 10
        assert deadline.day == 5
        assert deadline.hour == 14
        assert deadline.minute == 0
    
    def test_parse_deadline_relative(self):
        """Тест парсинга относительных дат."""
        # Тест с завтра
        deadline = ParsingService.parse_deadline("завтра")
        assert deadline is not None
        assert deadline > datetime.now()
    
    def test_parse_deadline_invalid(self):
        """Тест парсинга невалидных дат."""
        assert ParsingService.parse_deadline("вчера") is None
        assert ParsingService.parse_deadline("abc") is None
        assert ParsingService.parse_deadline("") is None
    
    def test_validate_contact_info_valid(self):
        """Тест валидации валидных контактов."""
        assert ParsingService.validate_contact_info("Иван, +7-900-123-45-67") is True
        assert ParsingService.validate_contact_info("@username") is True
        assert ParsingService.validate_contact_info("email@example.com") is True
        assert ParsingService.validate_contact_info("Имя: Иван\nТелефон: +7-900-123-45-67") is True
    
    def test_validate_contact_info_invalid(self):
        """Тест валидации невалидных контактов."""
        assert ParsingService.validate_contact_info("") is False
        assert ParsingService.validate_contact_info("Иван") is False  # Только имя
        assert ParsingService.validate_contact_info("ab") is False  # Слишком короткое