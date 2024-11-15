import enum
from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String, Enum

# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, DeclarativeBase

# Base = declarative_base()


class Base(DeclarativeBase):
    pass


class Role(enum.Enum):
    admin = "admin"
    moderator = "moderator"
    user = "user"


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    fullname = Column(String(150))
    phone_number = Column(String(20))
    email = Column(String(150), unique=True, index=True)
    birthday = Column(Date)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="contacts")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    refresh_token = Column(String(255), nullable=True)
    contacts = relationship("Contact", back_populates="user")
    confirmed = Column(Boolean, default=False)
    avatar = Column(String(255), nullable=True)
    role = Column(Enum(Role), default=Role.user, nullable=True)
