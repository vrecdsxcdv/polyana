"""
Модели базы данных для бота типографии.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, BigInteger
from sqlalchemy.orm import relationship

from database import Base


class OrderStatus(str, Enum):
    """Статусы заказа."""
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_CLIENT = "WAITING_CLIENT"
    READY = "READY"
    CANCELLED = "CANCELLED"


class User(Base):
    """Модель пользователя."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    tg_user_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    orders = relationship("Order", back_populates="user")


class Order(Base):
    """Модель заказа."""
    
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Параметры заказа
    what_to_print = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    format = Column(String(100), nullable=True)  # "A4 210×297" или "90×50"
    sides = Column(String(20), nullable=True)  # '1' | '2'
    color = Column(String(20), nullable=True)   # '4+0' | '4+4' | '1+0' etc.
    paper = Column(String(255), nullable=True)  # "300 г/м²" для визиток
    finishing = Column(Text, nullable=True)
    has_layout = Column(String(50), nullable=True)  # 'yes' | 'no' | 'need_designer'
    deadline_at = Column(DateTime, nullable=True)
    contact = Column(String(255), nullable=True)
    comments = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)  # дополнительные пожелания
    
    # Статус и флаги
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.NEW, nullable=False)
    needs_operator = Column(Boolean, default=False, nullable=False)
    username = Column(String(255), nullable=True)  # username пользователя для отображения
    
    # Новые поля для постобработки и форматов
    lamination = Column(String(20), default='none', nullable=False)  # 'none'|'matte'|'glossy'
    bigovka_count = Column(Integer, default=0, nullable=False)  # 0-5
    corner_rounding = Column(Boolean, default=False, nullable=False)  # 0/1
    sheet_format = Column(String(20), default='', nullable=True)  # 'A5'|'A4'|'A3'|'custom'
    custom_size_mm = Column(String(50), default='', nullable=True)  # 'ШxВ' мм для пользовательского размера
    material = Column(String(50), default='', nullable=True)  # 'paper'|'vinyl' для наклеек
    print_color = Column(String(20), default='color', nullable=False)  # 'color'|'bw'
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="orders")
    attachments = relationship("Attachment", back_populates="order", cascade="all, delete-orphan")


class Attachment(Base):
    """Модель вложения к заказу."""
    
    __tablename__ = "attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    file_id = Column(String(255), nullable=False)  # Telegram file_id
    file_unique_id = Column(String(255), nullable=True)
    original_name = Column(String(255), nullable=True)
    mime = Column(String(100), nullable=True)
    mime_type = Column(String(100), nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    size = Column(BigInteger, nullable=True)  # Дублируем для совместимости
    tg_message_id = Column(Integer, nullable=True)
    from_chat_id = Column(BigInteger, nullable=True)  # ID чата, откуда пришел файл
    kind = Column(String(50), nullable=True, default="document")  # 'document'|'photo'
    path = Column(String(500), nullable=True)      # Локальный путь
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    order = relationship("Order", back_populates="attachments")