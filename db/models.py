from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    tg_user_id = Column(Integer, index=True, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="user", cascade="all,delete-orphan")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    what_to_print = Column(String(100), nullable=False)
    quantity = Column(Integer, default=0)
    format = Column(String(50), default="")
    sides = Column(String(10), default="")
    paper = Column(String(50), default="")
    deadline_at = Column(DateTime, nullable=True)
    contact = Column(String(50), default="")
    notes = Column(Text, default="")
    lamination = Column(String(20), default="none")
    bigovka_count = Column(Integer, default=0)
    corner_rounding = Column(Boolean, default=False)
    sheet_format = Column(String(20), default="")
    custom_size_mm = Column(String(50), default="")
    material = Column(String(20), default="")
    print_color = Column(String(10), default="color")
    status = Column(String(20), default="NEW")
    needs_operator = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="orders")
