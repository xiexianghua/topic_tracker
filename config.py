import os
from datetime import timedelta

class Config:
    # 数据库配置 - 数据库文件存储在data子目录下
    DATABASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(DATABASE_DIR, exist_ok=True)  # 确保目录存在
    DATABASE_URL = f'sqlite:///{os.path.join(DATABASE_DIR, "topic_tracker.db")}'
    
    # Google AI配置
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyCPs6vZBxhIn_jqsg4VFbSSDg5ZTBkhWCA')
    
    # 数据保留时间（天）
    DATA_RETENTION_DAYS = 2
    
    # RSS配置 - 使用环境变量或默认值
    RSS_HOST = os.getenv('RSS_HOST', 'http://localhost:5000')
    RSS_TITLE = "话题追踪订阅"
    RSS_DESCRIPTION = "基于AI的话题追踪RSS订阅"
    RSS_LINK = RSS_HOST