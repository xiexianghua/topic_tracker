from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime, timedelta
import logging
import pytz

logger = logging.getLogger(__name__)

class TopicScheduler:
    def __init__(self, db_url):
        jobstores = {
            'default': SQLAlchemyJobStore(url=db_url)
        }
        
        # 限制线程池大小，减少内存占用
        executors = {
            'default': ThreadPoolExecutor(max_workers=2)
        }
        
        job_defaults = {
            'coalesce': True,
            'max_instances': 1,
            'misfire_grace_time': 30
        }
        
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=pytz.timezone('Asia/Shanghai')  # 使用北京时间
        )
    
    def start(self):
        self.scheduler.start()
    
    def shutdown(self):
        self.scheduler.shutdown(wait=False)  # 不等待作业完成，快速关闭
    
    def add_topic_job(self, topic_id, search_interval, search_func):
        """添加话题搜索任务"""
        job_id = f"topic_{topic_id}"
        
        # 添加或更新任务（使用replace_existing）
        self.scheduler.add_job(
            search_func,
            'interval',
            seconds=search_interval,
            id=job_id,
            args=[topic_id],
            next_run_time=datetime.now(pytz.timezone('Asia/Shanghai')) + timedelta(seconds=10),  # 10秒后首次执行
            replace_existing=True  # 如果存在则替换
        )
        
        logger.info(f"添加/更新任务: {job_id}, 间隔: {search_interval}秒")
    
    def remove_topic_job(self, topic_id):
        """移除话题搜索任务"""
        job_id = f"topic_{topic_id}"
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"移除任务: {job_id}")
        except:
            pass