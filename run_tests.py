"""
Скрипт для запуска тестов.
"""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """Запускает тесты."""
    try:
        # Устанавливаем переменные окружения для тестов
        import os
        os.environ['TESTING'] = 'true'
        
        # Запускаем pytest
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/', 
            '-v', 
            '--tb=short',
            '--cov=services',
            '--cov-report=term-missing'
        ], cwd=Path(__file__).parent)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Ошибка при запуске тестов: {e}")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
