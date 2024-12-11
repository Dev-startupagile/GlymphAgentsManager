from sqlalchemy import ForeignKey, Column, Integer, String
from sqlalchemy.orm import relationship
from users import User
from database.base import Base

class RoleAssignment(Base):
    __tablename__ = "role_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_name = Column(String(50), nullable=False)
    user = relationship("User", back_populates="roles")

User.roles = relationship("RoleAssignment", back_populates="user")
