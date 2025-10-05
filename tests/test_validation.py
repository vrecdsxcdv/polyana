"""
Тесты для валидации данных.
"""

import pytest
from services.files import FileService
from config import config


class TestValidation:
    """Тесты для валидации."""
    
    def test_validate_file_valid(self):
        """Тест валидации валидного файла."""
        file_service = FileService()
        is_valid, error = file_service.validate_file(
            "document.pdf", "application/pdf", 1024 * 1024  # 1 МБ
        )
        assert is_valid is True
        assert error is None
    
    def test_validate_file_too_large(self):
        """Тест валидации слишком большого файла."""
        file_service = FileService()
        is_valid, error = file_service.validate_file(
            "document.pdf", "application/pdf", 50 * 1024 * 1024  # 50 МБ
        )
        assert is_valid is False
        assert "слишком большой" in error
    
    def test_validate_file_invalid_extension(self):
        """Тест валидации файла с недопустимым расширением."""
        file_service = FileService()
        is_valid, error = file_service.validate_file(
            "document.txt", "text/plain", 1024
        )
        assert is_valid is False
        assert "Неподдерживаемый тип файла" in error
    
    def test_validate_file_invalid_mime(self):
        """Тест валидации файла с недопустимым MIME типом."""
        file_service = FileService()
        is_valid, error = file_service.validate_file(
            "document.pdf", "application/octet-stream", 1024
        )
        assert is_valid is False
        assert "Неподдерживаемый тип файла" in error
