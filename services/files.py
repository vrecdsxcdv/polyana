"""
Сервис работы с файлами.
"""

import os
import mimetypes
from pathlib import Path
from typing import Optional, Tuple

from telegram import Bot
from config import config


class FileService:
    """Сервис работы с файлами."""
    
    def __init__(self):
        """Инициализация сервиса."""
        self.uploads_dir = Path(config.UPLOADS_DIR)
        self.uploads_dir.mkdir(exist_ok=True)
    
    def validate_file(self, file_name: str, mime_type: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """Валидирует загружаемый файл."""
        # Проверяем размер файла
        if file_size > config.MAX_UPLOAD_BYTES:
            return False, f"Файл слишком большой. Максимальный размер: {config.MAX_UPLOAD_MB} МБ"
        
        # Проверяем расширение файла
        file_ext = Path(file_name).suffix.lower()
        if file_ext not in config.ALLOWED_EXTENSIONS:
            allowed_exts = ", ".join(config.ALLOWED_EXTENSIONS)
            return False, f"Неподдерживаемый тип файла. Разрешены: {allowed_exts}"
        
        # Проверяем MIME тип
        if mime_type and mime_type not in config.ALLOWED_MIME_TYPES:
            return False, "Неподдерживаемый тип файла"
        
        return True, None
    
    def get_file_path(self, user_id: int, order_code: str, file_name: str) -> Path:
        """Получает путь для сохранения файла."""
        user_dir = self.uploads_dir / str(user_id)
        order_dir = user_dir / str(order_code)
        order_dir.mkdir(parents=True, exist_ok=True)
        
        return order_dir / file_name
    
    async def save_file(self, bot: Bot, file_id: str, user_id: int, order_code: str, original_name: str) -> Tuple[bool, Optional[str], Optional[Path]]:
        """Сохраняет файл на диск."""
        try:
            # Получаем информацию о файле
            file_info = await bot.get_file(file_id)
            
            # Проверяем файл
            is_valid, error_msg = self.validate_file(
                original_name,
                file_info.file_path.split('.')[-1] if file_info.file_path else None,
                file_info.file_size or 0
            )
            
            if not is_valid:
                return False, error_msg, None
            
            # Получаем путь для сохранения
            file_path = self.get_file_path(user_id, order_code, original_name)
            
            # Скачиваем файл
            await file_info.download_to_drive(file_path)
            
            return True, None, file_path
            
        except Exception as e:
            return False, f"Ошибка при сохранении файла: {str(e)}", None
    
    def get_file_info(self, file_path: Path) -> dict:
        """Получает информацию о файле."""
        if not file_path.exists():
            return {}
        
        stat = file_path.stat()
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        return {
            'size_bytes': stat.st_size,
            'mime_type': mime_type,
            'created_at': stat.st_ctime,
            'modified_at': stat.st_mtime
        }
    
    def delete_file(self, file_path: Path) -> bool:
        """Удаляет файл."""
        try:
            if file_path.exists():
                file_path.unlink()
                return True
        except Exception:
            pass
        
        return False
    
    def cleanup_user_files(self, user_id: int) -> int:
        """Очищает все файлы пользователя."""
        user_dir = self.uploads_dir / str(user_id)
        deleted_count = 0
        
        if user_dir.exists():
            try:
                for file_path in user_dir.rglob('*'):
                    if file_path.is_file():
                        file_path.unlink()
                        deleted_count += 1
                
                # Удаляем пустые директории
                for dir_path in user_dir.rglob('*'):
                    if dir_path.is_dir() and not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        
            except Exception:
                pass
        
        return deleted_count