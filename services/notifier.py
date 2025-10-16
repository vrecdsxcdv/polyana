import os
from typing import Iterable, List, Tuple
from loguru import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError, BadRequest, Forbidden
from services.formatting import format_order_summary

def _parse_operator_ids() -> List[int]:
    """
    Собирает список ID из OPERATOR_IDS (через запятую) и OPERATOR_CHAT_ID (одиночный).
    Игнорирует пустые/мусорные значения. Возвращает уникальные int.
    """
    raw = []
    ids_env = os.getenv("OPERATOR_IDS", "")
    if ids_env:
        raw += [x.strip() for x in ids_env.split(",")]
    single = os.getenv("OPERATOR_CHAT_ID", "")
    if single:
        raw.append(single.strip())

    result = []
    for x in raw:
        if not x:
            continue
        try:
            result.append(int(x))
        except ValueError:
            logger.warning(f"Skip invalid OPERATOR id: {x!r}")
    # уникальные, порядок сохраняем
    uniq = []
    for x in result:
        if x not in uniq:
            uniq.append(x)
    return uniq

async def send_order_to_operators(bot, order, user, operator_chat_id, code):
    """Отправляет заказ в операторскую группу с кнопками статусов"""
    # Формируем карточку заказа
    order_summary = format_order_summary(order.__dict__ if hasattr(order, '__dict__') else order)
    
    # Добавляем информацию о пользователе
    user_info = f"👤 Клиент: {user.first_name or 'Пользователь'}"
    if user.username:
        user_info += f" (@{user.username})"
    user_info += f" (ID: {user.id})"
    
    text = f"📦 Новый заказ\n\n{order_summary}\n\n{user_info}\n\n🔢 Код заказа: <code>{code}</code>"
    
    # Создаем кнопки для управления статусом заказа
    keyboard = [
        [
            InlineKeyboardButton("📦 Взять", callback_data=f"take_order_{code}"),
            InlineKeyboardButton("⚙️ В работе", callback_data=f"start_work_{code}"),
            InlineKeyboardButton("✅ Готово", callback_data=f"complete_order_{code}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Используем новую функцию для отправки
    results = await send_order_to_operators_universal(
        bot=bot,
        text=text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    # Отправляем PDF файлы, если есть
    if hasattr(order, 'attachments') and order.attachments:
        for attachment in order.attachments:
            try:
                # Отправляем файлы во все успешные чаты
                for chat_id, success, _ in results:
                    if success:
                        try:
                            await bot.send_document(
                                chat_id=chat_id,
                                document=attachment.get('file_id'),
                                caption="📎 Макет PDF"
                            )
                        except Exception as e:
                            logger.error(f"Error sending attachment to chat_id={chat_id}: {e}")
            except Exception as e:
                logger.error(f"Error processing attachment: {e}")
    
    return results

async def send_order_to_operators(bot, text, reply_markup=None, parse_mode=None):
    """Resilient function to send order to operators chat"""
    # Import OPERATOR_CHAT_ID from app.py
    from app import OPERATOR_CHAT_ID
    
    if not OPERATOR_CHAT_ID:
        logger.warning("OPERATOR_CHAT_ID not set — skipping send to operators")
        return None
    try:
        msg = await bot.send_message(
            chat_id=int(OPERATOR_CHAT_ID),
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            disable_web_page_preview=True,
        )
        return msg
    except (BadRequest, Forbidden) as e:
        logger.error(f"Failed to send to operators chat {OPERATOR_CHAT_ID}: {e}")
        return None

async def send_order_to_operators_universal(bot, text: str, reply_markup=None, parse_mode=None) -> List[Tuple[int, bool, str]]:
    """
    NEW: Пытается отправить сообщение операторскому чату.
    Возвращает список (chat_id, success, error_message).
    Не выбрасывает исключения наружу.
    """
    results: List[Tuple[int, bool, str]] = []
    
    # NEW: Используем env_int helper для получения OPERATOR_CHAT_ID
    from app import env_int
    op_chat = env_int("OPERATOR_CHAT_ID")
    if op_chat is None:
        logger.warning("OPERATOR_CHAT_ID is not set; skip notifying operators")
        return []

    try:
        await bot.send_message(
            chat_id=op_chat,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            disable_web_page_preview=True,
        )
        results.append((op_chat, True, ""))
    except (BadRequest, TelegramError) as e:
        logger.error(f"Failed to send order to operators (chat {op_chat}): {e}")
        results.append((op_chat, False, str(e)))
    except Exception as e:
        logger.exception(f"Unexpected error notifying operator chat_id={op_chat}: {e}")
        results.append((op_chat, False, str(e)))
    return results