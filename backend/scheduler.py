from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import subprocess
import sys
import os
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone='Asia/Shanghai')  # 设置为北京时间
        self.jobs = {}
    
    def start(self):
        """启动调度器"""
        self.scheduler.start()
        logger.info("任务调度器已启动（北京时间）")
    
    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("任务调度器已停止")
    
    def add_job(self, script_id, cron_expression):
        """添加定时任务
        
        Args:
            script_id: 脚本ID
            cron_expression: cron表达式，如 "0 9 * * *" 表示每天9点
        """
        if script_id in self.jobs:
            self.remove_job(script_id)
        
        if not cron_expression:
            logger.warning(f"脚本ID={script_id} 没有设置cron表达式")
            return
        
        try:
            # 解析cron表达式
            cron_parts = cron_expression.strip().split()
            if len(cron_parts) != 5:
                logger.error(f"无效的cron表达式: {cron_expression}")
                return
            
            minute, hour, day, month, day_of_week = cron_parts
            
            # 创建cron触发器
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                timezone='Asia/Shanghai'  # 使用北京时间
            )
            
            # 添加任务
            job = self.scheduler.add_job(
                func=self.run_script,
                trigger=trigger,
                args=[script_id],
                id=str(script_id),
                replace_existing=True
            )
            
            self.jobs[script_id] = job
            logger.info(f"已添加定时任务: 脚本ID={script_id}, Cron={cron_expression}")
            
            # 获取下次运行时间
            next_run = job.next_run_time
            if next_run:
                logger.info(f"下次运行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
            
        except Exception as e:
            logger.error(f"添加定时任务失败: {e}")
    
    def remove_job(self, script_id):
        """移除定时任务"""
        if script_id in self.jobs:
            try:
                self.scheduler.remove_job(str(script_id))
                del self.jobs[script_id]
                logger.info(f"已移除定时任务: 脚本ID={script_id}")
            except Exception as e:
                logger.error(f"移除定时任务失败: {e}")
    
    def get_next_run_time(self, script_id):
        """获取下次运行时间"""
        if script_id in self.jobs:
            job = self.jobs[script_id]
            if job.next_run_time:
                return job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
        return None
    
    def run_script(self, script_id):
        """执行脚本"""
        from app import app
        from models import db, Script, ScriptRun
        
        with app.app_context():
            script = Script.query.get(script_id)
            if not script:
                logger.error(f"脚本不存在: ID={script_id}")
                return
            
            # 创建运行记录
            run = ScriptRun(script_id=script_id)
            db.session.add(run)
            db.session.commit()
            
            logger.info(f"开始执行脚本: {script.name}")
            
            try:
                # 获取当前项目目录
                current_dir = os.path.dirname(os.path.abspath(__file__))
                
                # 构建包含导入路径的脚本
                script_with_imports = f"""
import sys
import os

# 添加项目目录到Python路径
sys.path.insert(0, r'{current_dir}')

# 设置环境变量（如果脚本中使用了）
os.environ['GEMINI_API_KEY'] = os.environ.get('GEMINI_API_KEY', '')
os.environ['BARK_DEVICE_KEY'] = os.environ.get('BARK_DEVICE_KEY', '')
os.environ['BARK_API_SERVER'] = os.environ.get('BARK_API_SERVER', '')

# 执行用户脚本
{script.code}
"""
                
                # 执行脚本
                result = subprocess.run(
                    [sys.executable, '-c', script_with_imports],
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5分钟超时
                    env=os.environ.copy()  # 传递环境变量
                )
                
                run.output = result.stdout
                run.error = result.stderr
                run.status = 'success' if result.returncode == 0 else 'failed'
                run.completed_at = datetime.now(timezone.utc)
                
                logger.info(f"脚本执行完成: {script.name}, 状态={run.status}")
                
            except subprocess.TimeoutExpired:
                run.error = "Script execution timeout"
                run.status = 'failed'
                run.completed_at = datetime.now(timezone.utc)
                logger.error(f"脚本执行超时: {script.name}")
            except Exception as e:
                run.error = str(e)
                run.status = 'failed'
                run.completed_at = datetime.now(timezone.utc)
                logger.error(f"脚本执行错误: {script.name}, 错误={str(e)}")
            
            db.session.commit()