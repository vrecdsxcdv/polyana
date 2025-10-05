"""
Тесты на устойчивость FSM и обработчиков.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, Message, User, Chat, CallbackQuery
from telegram.ext import ContextTypes

from handlers.order_flow import handle_what_to_print, handle_quantity, handle_cancel, handle_back
from keyboards import norm, alias_map, BTN_BACK, BTN_CANCEL
from states import OrderStates


class TestRobustness:
    """Тесты на устойчивость обработчиков."""
    
    @pytest.fixture
    def mock_update(self):
        """Создает мок Update."""
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 12345
        update.effective_chat = MagicMock(spec=Chat)
        update.effective_chat.id = 12345
        update.message = MagicMock(spec=Message)
        update.message.text = "test"
        update.message.reply_text = AsyncMock()
        update.callback_query = None
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Создает мок Context."""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        context.bot = MagicMock()
        context.bot.send_message = AsyncMock()
        return context
    
    def test_norm_function(self):
        """Тест функции нормализации."""
        assert norm("  Test  ") == "test"
        assert norm("TEST") == "test"
        assert norm("") == ""
        assert norm(None) == ""
    
    def test_alias_map_function(self):
        """Тест функции алиасов."""
        assert alias_map("двусторонняя") == "2-sided"
        assert alias_map("2-сторонняя") == "2-sided"
        assert alias_map("цветная") == "4+4"
        assert alias_map("ч/б") == "1+0"
        assert alias_map("да") == "yes"
        assert alias_map("нет") == "no"
        assert alias_map("unknown") == "unknown"
    
    @pytest.mark.asyncio
    async def test_handle_cancel(self, mock_update, mock_context):
        """Тест обработки отмены."""
        result = await handle_cancel(mock_update, mock_context)
        
        assert result == -1  # ConversationHandler.END
        mock_update.message.reply_text.assert_called_once()
        assert mock_context.user_data == {}
    
    @pytest.mark.asyncio
    async def test_handle_back_first_step(self, mock_update, mock_context):
        """Тест возврата с первого шага."""
        result = await handle_back(mock_update, mock_context, OrderStates.WHAT_TO_PRINT)
        
        assert result == -1  # ConversationHandler.END
        mock_update.message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_what_to_print_cancel(self, mock_update, mock_context):
        """Тест отмены на шаге выбора типа печати."""
        mock_update.message.text = BTN_CANCEL
        
        result = await handle_what_to_print(mock_update, mock_context)
        
        assert result == -1  # ConversationHandler.END
        mock_update.message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_what_to_print_back(self, mock_update, mock_context):
        """Тест возврата на шаге выбора типа печати."""
        mock_update.message.text = BTN_BACK
        
        result = await handle_what_to_print(mock_update, mock_context)
        
        assert result == -1  # ConversationHandler.END
        mock_update.message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_what_to_print_valid_input(self, mock_update, mock_context):
        """Тест валидного ввода на шаге выбора типа печати."""
        mock_update.message.text = "Визитки"
        
        result = await handle_what_to_print(mock_update, mock_context)
        
        assert result == OrderStates.QUANTITY
        assert mock_context.user_data["what_to_print"] == "Визитки"
        mock_update.message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_what_to_print_invalid_input(self, mock_update, mock_context):
        """Тест невалидного ввода на шаге выбора типа печати."""
        mock_update.message.text = "случайный текст"
        
        result = await handle_what_to_print(mock_update, mock_context)
        
        assert result == OrderStates.WHAT_TO_PRINT
        mock_update.message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_quantity_cancel(self, mock_update, mock_context):
        """Тест отмены на шаге ввода тиража."""
        mock_update.message.text = BTN_CANCEL
        
        result = await handle_quantity(mock_update, mock_context)
        
        assert result == -1  # ConversationHandler.END
        mock_update.message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_quantity_valid_input(self, mock_update, mock_context):
        """Тест валидного ввода на шаге ввода тиража."""
        mock_update.message.text = "100"
        
        result = await handle_quantity(mock_update, mock_context)
        
        assert result == OrderStates.FORMAT
        assert mock_context.user_data["quantity"] == 100
        mock_update.message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_quantity_invalid_input(self, mock_update, mock_context):
        """Тест невалидного ввода на шаге ввода тиража."""
        mock_update.message.text = "не число"
        
        result = await handle_quantity(mock_update, mock_context)
        
        assert result == OrderStates.QUANTITY
        mock_update.message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_quantity_with_aliases(self, mock_update, mock_context):
        """Тест ввода тиража с алиасами."""
        mock_update.message.text = " 100 штук "
        
        result = await handle_quantity(mock_update, mock_context)
        
        assert result == OrderStates.FORMAT
        assert mock_context.user_data["quantity"] == 100
    
    @pytest.mark.asyncio
    async def test_handle_what_to_print_callback_query(self, mock_update, mock_context):
        """Тест обработки callback query."""
        # Создаем callback query
        callback_query = MagicMock(spec=CallbackQuery)
        callback_query.answer = AsyncMock()
        callback_query.edit_message_text = AsyncMock()
        callback_query.data = "business_cards"
        
        mock_update.callback_query = callback_query
        mock_update.message = None
        
        result = await handle_what_to_print(mock_update, mock_context)
        
        assert result == OrderStates.QUANTITY
        assert mock_context.user_data["what_to_print"] == "Визитки"
        callback_query.answer.assert_called_once()
        callback_query.edit_message_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_what_to_print_callback_other(self, mock_update, mock_context):
        """Тест обработки callback query с 'other'."""
        callback_query = MagicMock(spec=CallbackQuery)
        callback_query.answer = AsyncMock()
        callback_query.edit_message_text = AsyncMock()
        callback_query.data = "other"
        
        mock_update.callback_query = callback_query
        mock_update.message = None
        
        result = await handle_what_to_print(mock_update, mock_context)
        
        assert result == OrderStates.WHAT_TO_PRINT
        callback_query.answer.assert_called_once()
        callback_query.edit_message_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_update, mock_context):
        """Тест обработки ошибок."""
        # Симулируем ошибку
        mock_update.message.reply_text.side_effect = Exception("Test error")
        
        result = await handle_what_to_print(mock_update, mock_context)
        
        # Должен вернуть текущее состояние при ошибке
        assert result == OrderStates.WHAT_TO_PRINT
