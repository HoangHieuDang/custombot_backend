from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import Integer, String, DateTime, Float
from sqlalchemy import create_engine

engine = create_engine("sqlite:///custom_bot_db", echo=True)


class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100))
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime)


class RobotParts(Base):
    __tablename__ = "robot_parts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50),
                                      nullable=False)  # arm, shoulder arm, chest, skirt, upper_leg, leg, foot, backpack
    stl_path: Mapped[str] = mapped_column()
    img_path: Mapped[str] = mapped_column()
    price: Mapped[float] = mapped_column()


class CustomBots(Base):
    __tablename__ = "custom_bots"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(default="in_progress")  # in_progress, ordered
    created_at: Mapped[DateTime] = mapped_column(DateTime)
    total_price: Mapped[float] = mapped_column(default=0.0)


class CustomBotParts(Base):
    __tablename__ = "custom_bot_parts"
    custom_robot_id: Mapped[int] = mapped_column(ForeignKey("custom_bots.id"), primary_key=True)
    robot_part_id: Mapped[int] = mapped_column(ForeignKey("robot_parts.id"), primary_key=True)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    custom_robot_id: Mapped[int] = mapped_column(ForeignKey("custom_bots.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(default=1)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)  # custom bot price * quantity
    status: Mapped[str] = mapped_column(String(20), default="pending")  # e.g. pending, paid, shipped, canceled
    payment_method: Mapped[str] = mapped_column(String(50), nullable=True)  # e.g. credit_card, paypal, etc.
    shipping_address: Mapped[str] = mapped_column(String, nullable=True)
    shipping_date: Mapped[DateTime] = mapped_column(DateTime)
    created_at: Mapped[DateTime] = mapped_column(DateTime)

#Base.metadata.create_all(engine)