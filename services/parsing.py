"""
Сервис парсинга и валидации данных.
"""

import re
from datetime import datetime
from typing import Optional

import dateparser


class ParsingService:
    """Сервис парсинга и валидации."""
    
    @staticmethod
    def parse_quantity(text: str) -> Optional[int]:
        """Парсит количество из текста."""
        # Убираем все кроме цифр
        numbers = re.findall(r'\d+', text)
        if not numbers:
            return None
        
        try:
            quantity = int(numbers[0])
            # Проверяем разумные пределы
            if 1 <= quantity <= 100000:
                return quantity
        except ValueError:
            pass
        
        return None
    
    @staticmethod
    def parse_format(text: str) -> Optional[str]:
        """Парсит формат из текста."""
        # Стандартные форматы
        standard_formats = {
            'a4': 'A4 (210×297 мм)',
            'a5': 'A5 (148×210 мм)', 
            'a6': 'A6 (105×148 мм)',
            'a3': 'A3 (297×420 мм)'
        }
        
        text_lower = text.lower().strip()
        
        # Проверяем стандартные форматы
        for key, value in standard_formats.items():
            if key in text_lower:
                return value
        
        # Парсим размеры в формате "Ш×В мм" или "Ш x В мм"
        size_pattern = r'(\d+)\s*[×x]\s*(\d+)\s*мм?'
        match = re.search(size_pattern, text_lower)
        
        if match:
            width = int(match.group(1))
            height = int(match.group(2))
            return f"{width}×{height} мм"
        
        # Если не удалось распарсить, возвращаем как есть
        return text.strip() if text.strip() else None
    
    @staticmethod
    def parse_deadline(text: str) -> Optional[datetime]:
        """Парсит дедлайн из текста."""
        text = text.strip()
        
        # Пробуем парсить с помощью dateparser
        parsed_date = dateparser.parse(text, languages=['ru', 'en'])
        
        if parsed_date:
            # Проверяем, что дата не в прошлом
            if parsed_date > datetime.now():
                return parsed_date
        
        # Пробуем парсить вручную формат ДД.ММ.ГГГГ ЧЧ:ММ
        date_pattern = r'(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{2})'
        match = re.search(date_pattern, text)
        
        if match:
            try:
                day, month, year, hour, minute = map(int, match.groups())
                parsed_date = datetime(year, month, day, hour, minute)
                
                # Проверяем, что дата не в прошлом
                if parsed_date > datetime.now():
                    return parsed_date
            except ValueError:
                pass
        
        return None
    
    @staticmethod
    def validate_contact_info(text: str) -> bool:
        """Валидирует контактную информацию."""
        if not text or len(text.strip()) < 3:
            return False
        
        # Проверяем наличие хотя бы одного контакта
        has_phone = bool(re.search(r'[\+]?[0-9\s\-\(\)]{7,}', text))
        has_username = bool(re.search(r'@[a-zA-Z0-9_]+', text))
        has_email = bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))
        
        return has_phone or has_username or has_email