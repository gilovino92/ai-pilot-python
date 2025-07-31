from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, UUID
from sqlalchemy.orm import relationship
from app.tools.db import Base
from datetime import datetime
import uuid

class PilotChat(Base):
    __tablename__ = "pilot_chat"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    context = Column(JSON, nullable=True)
    serialized_context = Column(String, nullable=True)
    
    # Relationships with cascade delete
    messages = relationship("PilotChatMessage", back_populates="chat", cascade="all, delete-orphan", passive_deletes=True)


class PilotChatMessage(Base):
    __tablename__ = "pilot_chat_message"  # Updated to match migration

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    content = Column(Text, nullable=False)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    type = Column(String(50), nullable=False)  # 'user_query' or 'user_response' or 'agent_response' or 'agent_thinking'
    created_at = Column(DateTime, default=datetime.utcnow)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("pilot_chat.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    chat = relationship("PilotChat", back_populates="messages")
