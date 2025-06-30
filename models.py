from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone
import json

Base = declarative_base()

class Topic(Base):
    __tablename__ = 'topics'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    search_query = Column(Text, nullable=False)
    search_interval = Column(Integer, default=3600)  # 秒
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # 关系 - 使用lazy loading减少内存占用
    results = relationship("SearchResult", back_populates="topic", cascade="all, delete-orphan", lazy='dynamic')

class SearchResult(Base):
    __tablename__ = 'search_results'
    
    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey('topics.id'))
    content = Column(Text, nullable=False)
    raw_response = Column(Text)  # 存储原始响应
    is_duplicate = Column(Boolean, default=False)
    in_rss = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 关系
    topic = relationship("Topic", back_populates="results")

class Database:
    def __init__(self, db_url):
        # 使用StaticPool减少连接数，优化内存占用
        if 'sqlite' in db_url:
            self.engine = create_engine(
                db_url, 
                connect_args={'check_same_thread': False},
                poolclass=StaticPool,
                pool_pre_ping=True
            )
        else:
            self.engine = create_engine(
                db_url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600
            )
        
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self):
        return self.SessionLocal()