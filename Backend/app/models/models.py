from ..db.business_db import Base
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP


class User(Base):
    """
    User model for the application.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    # username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String, nullable=False)
    # is_active = Column(Boolean, default=True)
    gender = Column(String(10), nullable=True)  # e.g., "male", "female", "other"
    age = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))
    # clarifications = relationship("Clarification", back_populates="user", cascade="all, delete-orphan")


# class Clarification(Base):
#     __tablename__ = "clarifications"

#     id = Column(Integer, primary_key=True, nullable=False, index=True)
#     user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
#     type = Column(String(10), nullable=False)          # one of ["schedule","update","delete"]
#     query = Column(Text, nullable=False)
#     progress = Column(Text, nullable=False)
#     current_datetime = Column(String, nullable=False)  # ISO‐format datetime as string
#     email = Column(JSONB, nullable=True)               # serialized dict, nullable

#     # relationship back to User (optional)
#     user = relationship("User", back_populates="clarifications")
