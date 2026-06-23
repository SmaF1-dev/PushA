from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nickname = Column(String, nullable=False)
    riot_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("ValorantProfile", back_populates="player", uselist=False)

class ValorantProfile(Base):
    __tablename__ = "valorant_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), unique=True)
    region = Column(String, nullable=False)
    current_rank = Column(String, nullable=False) 
    main_roles = Column(String) 
    status = Column(String, default="OFFLINE") 
    teammate_rating = Column(Float, default=0.0)
    reviews_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    player = relationship("Player", back_populates="profile")

class TeammateReview(Base):
    __tablename__ = "teammate_reviews"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("players.id"))
    target_player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"))
    rating = Column(Integer, nullable=False) # 1-5
    comment = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)