#!/usr/bin/env bash
# Универсальный скрипт запуска printshop_bot

set -e
cd "$(dirname "$0")"

echo "🚀 Запуск printshop_bot..."

# Создаем виртуальное окружение если его нет
if [ ! -d venv ]; then 
    echo "📦 Создаем виртуальное окружение..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "🔧 Активируем виртуальное окружение..."
source venv/bin/activate

# Обновляем pip и устанавливаем зависимости
echo "📥 Устанавливаем зависимости..."
pip install --upgrade pip
pip install -r requirements.txt

# Проверяем окружение
echo "🔍 Проверяем окружение..."
python3 scripts/check_env.py

# Останавливаем дубликаты процессов
echo "🛑 Останавливаем дубликаты процессов..."
./scripts/kill_dupes.sh

# Запускаем бота
echo "🤖 Запускаем бота..."
python3 app.py
