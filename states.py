"""
Состояния FSM для диалога заказа.
"""

from enum import Enum


class OrderStates(str, Enum):
    """Состояния диалога заказа."""
    
    # Упрощенный поток
    PRODUCT = "product"
    BC_QTY = "bc_qty"
    BC_SIZE = "bc_size"
    BC_SIDES = "bc_sides"
    FLY_FORMAT = "fly_format"
    FLY_SIDES = "fly_sides"
    
    # Новые состояния для форматов и постобработки
    ORDER_SHEET_FORMAT = "order_sheet_format"
    ORDER_CUSTOM_SIZE = "order_custom_size"
    ORDER_POSTPRESS = "order_postpress"
    ORDER_POSTPRESS_BIGOVKA = "order_postpress_bigovka"
    ORDER_BANNER_SIZE = "order_banner_size"
    ORDER_MATERIAL = "order_material"
    ORDER_PRINT_COLOR = "order_print_color"
    PRINT_FORMAT = "print_format"
    PRINT_TYPE = "print_type"
    POSTPRESS = "postpress"
    CANCEL_CHOICE = "cancel_choice"
    
    ORDER_UPLOAD = "order_upload"
    ORDER_DUE = "order_due"
    ORDER_PHONE = "order_phone"
    ORDER_NOTES = "order_notes"
    ORDER_CONFIRM = "order_confirm"