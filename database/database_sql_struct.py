from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import Integer, String, DateTime, Float, Enum


class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime)


class RobotParts(Base):
    __tablename__ = "robot_parts"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(String(50),
                                      nullable=False)
    # "arm", "upper_arm", "lower_arm", "hand", "shoulder", "chest", "waist", "skirt", "upper_leg", "lower_leg","knee", "foot", "backpack"
    model_path: Mapped[str] = mapped_column()
    img_path: Mapped[str] = mapped_column()
    price: Mapped[float] = mapped_column()


class CustomBots(Base):
    __tablename__ = "custom_bots"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100))

    StatusEnum = Enum("in_progress", "ordered", name="custom_bot_status")
    status: Mapped[str] = mapped_column(StatusEnum, default="in_progress")  # in_progress, ordered
    created_at: Mapped[DateTime] = mapped_column(DateTime)


class CustomBotParts(Base):
    __tablename__ = "custom_bot_parts"
    custom_robot_id: Mapped[int] = mapped_column(ForeignKey("custom_bots.id"), primary_key=True)
    robot_part_id: Mapped[int] = mapped_column(ForeignKey("robot_parts.id"), primary_key=True)
    robot_part_amount: Mapped[int] = mapped_column(Integer, nullable=False)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    custom_robot_id: Mapped[int] = mapped_column(ForeignKey("custom_bots.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(default=1)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)  # custom bot price * quantity
    status: Mapped[str] = mapped_column(String(20), default="pending")  # e.g. pending, paid, shipped, cancelled
    payment_method: Mapped[str] = mapped_column(String(50), nullable=True)  # e.g. credit_card, paypal, etc.
    shipping_address: Mapped[str] = mapped_column(String, nullable=True)
    shipping_date: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime)


'''
#Run these lines of code 1 time to generate sqlite database
from sqlalchemy import create_engine
engine = create_engine("sqlite:///custom_bot_db", echo=True)
Base.metadata.create_all(engine)
'''
