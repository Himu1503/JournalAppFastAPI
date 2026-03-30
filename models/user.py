from database import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    journal_entries = relationship("JournalEntries", back_populates="user")