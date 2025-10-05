"""
Тесты для сервиса файлов.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock
from services.files import FileService


class TestFileService:
    """Тесты для FileService."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.file_service = FileService()
    
    def test_validate_file_valid(self):
        """Тест валидации валидного файла."""
        is_valid, error = self.file_service.validate_file(
            "document.pdf", "application/pdf", 1024 * 1024  # 1 МБ
        )
        assert is_valid is True
        assert error is None
    
    def test_validate_file_too_large(self):
        """Тест валидации слишком большого файла."""
        is_valid, error = self.file_service.validate_file(
            "document.pdf", "application/pdf", 50 * 1024 * 1024  # 50 МБ
        )
        assert is_valid is False
        assert "слишком большой" in error
    
    def test_validate_file_invalid_extension(self):
        """Тест валидации файла с недопустимым расширением."""
        is_valid, error = self.file_service.validate_file(
            "document.txt", "text/plain", 1024
        )
        assert is_valid is False
        assert "Неподдерживаемый тип файла" in error
    
    def test_validate_file_invalid_mime(self):
        """Тест валидации файла с недопустимым MIME типом."""
        is_valid, error = self.file_service.validate_file(
            "document.pdf", "application/octet-stream", 1024
        )
        assert is_valid is False
        assert "Неподдерживаемый тип файла" in error
    
    def test_get_file_path(self):
        """Тест получения пути к файлу."""
        path = self.file_service.get_file_path(12345, 67890, "document.pdf")
        expected_path = Path("uploads/12345/67890/document.pdf")
        assert path == expected_path
    
    def test_get_file_info_existing_file(self, tmp_path):
        """Тест получения информации о существующем файле."""
        # Создаем временный файл
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Получаем информацию о файле
        info = self.file_service.get_file_info(test_file)
        
        assert info['size_bytes'] > 0
        assert 'created_at' in info
        assert 'modified_at' in info
    
    def test_get_file_info_nonexistent_file(self):
        """Тест получения информации о несуществующем файле."""
        nonexistent_file = Path("nonexistent.txt")
        info = self.file_service.get_file_info(nonexistent_file)
        assert info == {}
    
    def test_delete_file_existing(self, tmp_path):
        """Тест удаления существующего файла."""
        # Создаем временный файл
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Удаляем файл
        result = self.file_service.delete_file(test_file)
        assert result is True
        assert not test_file.exists()
    
    def test_delete_file_nonexistent(self):
        """Тест удаления несуществующего файла."""
        nonexistent_file = Path("nonexistent.txt")
        result = self.file_service.delete_file(nonexistent_file)
        assert result is False
    
    def test_cleanup_user_files(self, tmp_path):
        """Тест очистки файлов пользователя."""
        # Создаем структуру директорий
        user_dir = tmp_path / "uploads" / "12345"
        user_dir.mkdir(parents=True)
        
        # Создаем файлы
        (user_dir / "file1.txt").write_text("content1")
        (user_dir / "file2.txt").write_text("content2")
        
        # Мокаем uploads_dir
        self.file_service.uploads_dir = tmp_path / "uploads"
        
        # Очищаем файлы пользователя
        deleted_count = self.file_service.cleanup_user_files(12345)
        
        assert deleted_count == 2
        # Директория может остаться, если в ней есть поддиректории
    
    def test_cleanup_user_files_nonexistent(self):
        """Тест очистки файлов несуществующего пользователя."""
        deleted_count = self.file_service.cleanup_user_files(99999)
        assert deleted_count == 0
