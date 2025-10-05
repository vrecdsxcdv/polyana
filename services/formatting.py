"""
Сервис форматирования карточек заказов и сообщений.
"""

from datetime import datetime
from typing import Optional

from models import Order, User
from texts import STATUS_LABELS


class FormattingService:
    """Сервис форматирования сообщений."""
    
    @staticmethod
    def format_order_card(order: Order, user: User, for_operator: bool = False) -> str:
        """Форматирует карточку заказа."""
        # Форматируем дедлайн
        deadline_str = "Не указан"
        if order.deadline_at:
            deadline_str = order.deadline_at.strftime("%d.%m.%Y %H:%M")
        
        # Форматируем имя пользователя
        user_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        if user.username:
            user_display = f"@{user.username} ({user_name})" if user_name else f"@{user.username}"
        else:
            user_display = user_name or "Не указано"
        
        # Форматируем макет
        layout_labels = {
            "yes": "✅ Есть",
            "no": "❌ Нет",
            "need_designer": "🎨 Нужен дизайнер"
        }
        layout_str = layout_labels.get(order.has_layout, order.has_layout)
        
        # Форматируем постобработку
        finishing_str = order.finishing or "Без обработки"
        
        # Форматируем новые поля постобработки
        lamination_labels = {
            "none": "нет",
            "matte": "мат",
            "glossy": "глянец"
        }
        lamination_str = lamination_labels.get(order.lamination, order.lamination)
        
        # Форматируем формат
        format_str = order.format
        if order.sheet_format == "custom" and order.custom_size_mm:
            format_str = f"Пользовательский: {order.custom_size_mm} мм"
        elif order.sheet_format:
            format_str = f"{order.sheet_format} ({order.format})"
        
        # Форматируем цветность
        color_labels = {
            "color": "Цветная",
            "bw": "Ч/Б"
        }
        color_str = color_labels.get(order.print_color, order.print_color)
        
        # Форматируем материал
        material_labels = {
            "paper": "Бумага",
            "vinyl": "Винил"
        }
        material_str = material_labels.get(order.material, order.material or "—")
        
        # Форматируем комментарии
        comments_str = order.comments or "Нет"
        
        card = f"""
📋 Заказ №{order.code}

🧾 Тип: {order.what_to_print}
📏 Формат: {format_str or '—'}
🖨️ Печать: {'Цветная' if order.print_color == 'color' else 'Ч/Б'}
✨ Ламинация: {lamination_str}
➖ Биговка: {order.bigovka_count or '—'}
🔘 Скругление углов: {'Да' if order.corner_rounding else 'Нет'}
📄 Материал: {material_str}
📅 Срок: {deadline_str}
📞 Контакт: {order.contact or '—'}
💬 Пожелания: {order.notes or '—'}
👤 Клиент: {user_display}
📊 Тираж: {order.quantity:,}
🔄 Стороны: {order.sides or '—'}
📄 Бумага: {order.paper or '—'}
✨ Постобработка: {finishing_str}
📁 Макет: {layout_str}
📊 Статус: {STATUS_LABELS.get(order.status.value, order.status.value)}
"""
        
        if for_operator:
            card += f"\n🆔 ID заказа: {order.id}"
            if order.needs_operator:
                card += "\n🚨 ТРЕБУЕТ ВНИМАНИЯ ОПЕРАТОРА"
        
        return card.strip()
    
    @staticmethod
    def format_order_summary(user_data: dict) -> str:
        """Форматирует сводку заказа для подтверждения."""
        lines = []
        
        lines.append(f"📦 Продукт: {user_data.get('what_to_print', 'Не указан')}")
        lines.append(f"📊 Количество: {user_data.get('quantity', 0)} шт")
        
        # Форматируем формат
        format_str = user_data.get('format', '')
        if user_data.get('sheet_format') == 'custom' and user_data.get('custom_size_mm'):
            format_str = f"Пользовательский: {user_data['custom_size_mm']} мм"
        elif user_data.get('sheet_format'):
            format_str = f"{user_data['sheet_format']} ({user_data.get('format', '')})"
        
        if format_str:
            lines.append(f"📐 Формат: {format_str}")
        
        if user_data.get('sides'):
            sides_text = "Двусторонняя" if user_data['sides'] == '2' else "Односторонняя"
            lines.append(f"🖨️ Печать: {sides_text}")
        
        if user_data.get('paper'):
            lines.append(f"📄 Бумага: {user_data['paper']}")
        
        # Новые поля постобработки
        lamination_labels = {
            "none": "нет",
            "matte": "мат", 
            "glossy": "глянец"
        }
        lamination = user_data.get('lamination', 'none')
        lines.append(f"🧾 Ламинация: {lamination_labels.get(lamination, lamination)}")
        
        bigovka_count = user_data.get('bigovka_count', 0)
        lines.append(f"📏 Биговка: {bigovka_count} линий")
        
        corner_rounding = user_data.get('corner_rounding', False)
        lines.append(f"🔲 Скругление углов: {'да' if corner_rounding else 'нет'}")
        
        # Материал и цветность
        material = user_data.get('material', '')
        if material:
            material_labels = {
                "paper": "Бумага",
                "vinyl": "Винил"
            }
            lines.append(f"📄 Материал: {material_labels.get(material, material)}")
        
        print_color = user_data.get('print_color', 'color')
        color_labels = {
            "color": "Цветная",
            "bw": "Ч/Б"
        }
        lines.append(f"🎨 Цветность: {color_labels.get(print_color, print_color)}")
        
        if user_data.get('deadline_at'):
            lines.append(f"🕒 Срок: {user_data['deadline_at'].strftime('%d.%m.%Y %H:%M')}")
        
        if user_data.get('contact'):
            lines.append(f"📞 Телефон: {user_data['contact']}")
        
        if user_data.get('notes'):
            lines.append(f"💬 Пожелания: {user_data['notes']}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_order_summary_old(order_data: dict) -> str:
        """Форматирует краткую сводку заказа для подтверждения."""
        deadline_str = "Не указан"
        if order_data.get("deadline_at"):
            if isinstance(order_data["deadline_at"], datetime):
                deadline_str = order_data["deadline_at"].strftime("%d.%m.%Y %H:%M")
            else:
                deadline_str = str(order_data["deadline_at"])
        
        layout_labels = {
            "yes": "✅ Есть",
            "no": "❌ Нет", 
            "need_designer": "🎨 Нужен дизайнер"
        }
        layout_str = layout_labels.get(order_data.get("has_layout", ""), order_data.get("has_layout", ""))
        
        return f"""
🖨️ Что печатать: {order_data.get('what_to_print', 'Не указано')}
📊 Тираж: {order_data.get('quantity', 0):,}
📐 Формат: {order_data.get('format', 'Не указано')}
🔄 Стороны: {order_data.get('sides', 'Не указано')}
🎨 Цветность: {order_data.get('color', 'Не указано')}
📄 Бумага: {order_data.get('paper', 'Не указано')}
✨ Постобработка: {order_data.get('finishing', 'Без обработки')}
📁 Макет: {layout_str}
⏰ Дедлайн: {deadline_str}
📞 Контакты: {order_data.get('contact', 'Не указано')}
💬 Комментарий: {order_data.get('comments', 'Нет')}
""".strip()