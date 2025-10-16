from enum import IntEnum

class OrderStates(IntEnum):
    # Общие состояния
    START = 1
    CHOOSE_CATEGORY = 10
    QUANTITY = 20
    
    # Офисная бумага
    OFFICE_FORMAT = 30        # A4 / A3
    OFFICE_COLOR = 40         # Ч/Б / Цветная
    
    # Плакаты
    POSTER_FORMAT = 50        # A2/A1/A0
    ORDER_POSTPRESS = 60      # Ламинация Да/Нет
    
    # Визитки
    BC_QTY = 70               # тираж визиток (кратно 50, min 50)
    BC_FORMAT = 80            # Визитка 90×50 (единственный формат)
    BC_SIDES = 90             # Односторонняя / Двусторонняя
    BC_LAMINATION = 100       # Матовая / Глянец
    
    # Флаеры
    FLY_FORMAT = 110          # A7/A6/A5/A4
    FLY_SIDES = 120           # Односторонняя / Двусторонняя
    
    # Наклейки
    STICKER_SIZE = 130        # ввод/кнопки размеров
    STICKER_MATERIAL = 140    # Бумага/Пленка
    STICKER_COLOR = 150       # Ч/Б / Цвет
    
    # Общие шаги
    ORDER_FILES = 160         # загрузка PDF
    ORDER_DUE = 170           # срок (dateparser)
    PHONE = 180               # телефон
    NOTES = 185               # дополнительные пожелания
    CONFIRM = 190             # подтверждение
    CANCEL_CONFIRM = 200      # подтверждение отмены (локальное состояние)

# обратная совместимость, если в коде встречалось CATEGORY
try:
    OrderStates.CATEGORY
except AttributeError:
    OrderStates.CATEGORY = OrderStates.CHOOSE_CATEGORY
