import uuid
import json
from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspaces = relationship("Workspace", back_populates="owner")

class Workspace(Base):
    __tablename__ = "workspaces"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="workspaces")
    documents = relationship("Document", back_populates="workspace")
    messages = relationship("Message", back_populates="workspace", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    cloudinary_url = Column(String, nullable=False)
    public_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="documents")

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)  # JSON string of cited sources
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="messages")