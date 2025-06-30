from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import logging
import json
import os
import pytz
import gc  # 添加垃圾回收

# 导入自定义模块
from config import Config
from models import Database, Topic, SearchResult
from llm_service import LLMService
from scheduler import TopicScheduler
from rss_generator import RSSGenerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化Flask应用
app = Flask(__name__)
CORS(app)

# 初始化配置
config = Config()

# 初始化服务
db = Database(config.DATABASE_URL)
llm_service = LLMService(config.GOOGLE_API_KEY)
scheduler = TopicScheduler(config.DATABASE_URL)
rss_generator = RSSGenerator(config.RSS_TITLE, config.RSS_DESCRIPTION, config.RSS_LINK)

# 定义北京时区
beijing_tz = pytz.timezone('Asia/Shanghai')

def get_beijing_time():
    """获取北京时间"""
    return datetime.now(beijing_tz)

def utc_to_beijing(utc_time):
    """UTC时间转北京时间"""
    if utc_time.tzinfo is None:
        utc_time = utc_time.replace(tzinfo=timezone.utc)
    return utc_time.astimezone(beijing_tz)

def search_topic_task(topic_id):
    """执行话题搜索任务"""
    session = db.get_session()
    try:
        topic = session.query(Topic).filter(Topic.id == topic_id).first()
        if not topic or not topic.is_active:
            return
        
        logger.info(f"开始搜索话题: {topic.name}")
        
        # 执行搜索
        content = llm_service.search_topic(topic.search_query)
        if not content:
            return
        
        # 保存结果（去除去重功能）
        result = SearchResult(
            topic_id=topic_id,
            content=content,
            is_duplicate=False,  # 不再进行去重检查
            in_rss=True  # 所有内容都加入RSS
        )
        session.add(result)
        session.commit()
        
        logger.info(f"话题 {topic.name} 搜索完成")
        
    except Exception as e:
        logger.error(f"搜索任务失败: {str(e)}")
        session.rollback()
    finally:
        session.close()
        # 强制垃圾回收
        gc.collect()

def clean_old_data():
    """清理过期数据"""
    session = db.get_session()
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=config.DATA_RETENTION_DAYS)
        deleted = session.query(SearchResult).filter(
            SearchResult.created_at < cutoff_date
        ).delete()
        session.commit()
        logger.info(f"清理了 {deleted} 条过期数据")
    except Exception as e:
        logger.error(f"清理数据失败: {str(e)}")
        session.rollback()
    finally:
        session.close()
        # 强制垃圾回收
        gc.collect()

# 路由定义
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/topics', methods=['GET', 'POST'])
def topics():
    session = db.get_session()
    
    try:
        if request.method == 'GET':
            topics = session.query(Topic).all()
            result = [{
                'id': t.id,
                'name': t.name,
                'search_query': t.search_query,
                'search_interval': t.search_interval,
                'is_active': t.is_active,
                'created_at': utc_to_beijing(t.created_at).isoformat()
            } for t in topics]
            return jsonify(result)
        
        elif request.method == 'POST':
            data = request.json
            topic = Topic(
                name=data['name'],
                search_query=data['search_query'],
                search_interval=data.get('search_interval', 3600)
            )
            session.add(topic)
            session.commit()
            
            # 添加定时任务
            scheduler.add_topic_job(topic.id, topic.search_interval, search_topic_task)
            
            result = {'id': topic.id, 'message': '话题创建成功'}
            return jsonify(result), 201
    finally:
        session.close()

@app.route('/api/topics/<int:topic_id>', methods=['PUT', 'DELETE'])
def topic_detail(topic_id):
    session = db.get_session()
    
    try:
        topic = session.query(Topic).filter(Topic.id == topic_id).first()
        
        if not topic:
            return jsonify({'error': '话题不存在'}), 404
        
        if request.method == 'PUT':
            data = request.json
            topic.name = data.get('name', topic.name)
            topic.search_query = data.get('search_query', topic.search_query)
            topic.search_interval = data.get('search_interval', topic.search_interval)
            topic.is_active = data.get('is_active', topic.is_active)
            
            session.commit()
            
            # 更新定时任务
            if topic.is_active:
                scheduler.add_topic_job(topic.id, topic.search_interval, search_topic_task)
            else:
                scheduler.remove_topic_job(topic.id)
            
            return jsonify({'message': '话题更新成功'})
        
        elif request.method == 'DELETE':
            scheduler.remove_topic_job(topic.id)
            session.delete(topic)
            session.commit()
            return jsonify({'message': '话题删除成功'})
    finally:
        session.close()

@app.route('/api/results/<int:topic_id>')
def get_results(topic_id):
    session = db.get_session()
    
    try:
        results = session.query(SearchResult).filter(
            SearchResult.topic_id == topic_id
        ).order_by(SearchResult.created_at.desc()).limit(50).all()
        
        result = [{
            'id': r.id,
            'content': r.content,
            'is_duplicate': r.is_duplicate,
            'in_rss': r.in_rss,
            'created_at': utc_to_beijing(r.created_at).isoformat()
        } for r in results]
        
        return jsonify(result)
    finally:
        session.close()

@app.route('/rss')
def rss_feed():
    session = db.get_session()
    
    try:
        # 获取RSS条目 - 确保按created_at降序排序
        results = session.query(SearchResult).join(Topic).filter(
            SearchResult.in_rss == True,
            SearchResult.created_at >= datetime.now(timezone.utc) - timedelta(days=7)
        ).order_by(SearchResult.created_at.desc()).limit(50).all()
        
        items = [{
            'id': r.id,
            'topic_name': r.topic.name,
            'content': r.content,
            'created_at': r.created_at
        } for r in results]
        
        # 生成RSS
        rss_content = rss_generator.generate_feed(items)
        return Response(rss_content, mimetype='application/rss+xml')
    finally:
        session.close()

@app.route('/rss/<int:topic_id>')
def topic_rss_feed(topic_id):
    """单个话题的RSS订阅"""
    session = db.get_session()
    
    try:
        # 获取话题信息
        topic = session.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            return "话题不存在", 404
        
        # 获取该话题的RSS条目 - 确保按created_at降序排序
        results = session.query(SearchResult).filter(
            SearchResult.topic_id == topic_id,
            SearchResult.in_rss == True,
            SearchResult.created_at >= datetime.now(timezone.utc) - timedelta(days=7)
        ).order_by(SearchResult.created_at.desc()).limit(50).all()
        
        items = [{
            'id': r.id,
            'topic_name': topic.name,
            'content': r.content,
            'created_at': r.created_at
        } for r in results]
        
        # 为单个话题生成RSS
        topic_rss_generator = RSSGenerator(
            f"{topic.name} - 话题追踪",
            f"关于 {topic.name} 的最新内容追踪",
            f"{config.RSS_LINK}/rss/{topic_id}"
        )
        rss_content = topic_rss_generator.generate_feed(items)
        return Response(rss_content, mimetype='application/rss+xml')
    finally:
        session.close()

@app.route('/api/trigger/<int:topic_id>', methods=['POST'])
def trigger_search(topic_id):
    """手动触发搜索"""
    search_topic_task(topic_id)
    return jsonify({'message': '搜索已触发'})

# 启动应用
if __name__ == '__main__':
    import os
    
    # 打印数据库文件位置
    db_path = config.DATABASE_URL.replace('sqlite:///', '')
    print(f"数据库文件位置: {db_path}")
    
    # 检查是否是重新加载（Flask开发模式）
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        # 启动调度器
        scheduler.start()
        
        # 添加数据清理任务（使用replace_existing避免重复）
        scheduler.scheduler.add_job(
            clean_old_data,
            'interval',
            days=1,
            id='clean_old_data',
            next_run_time=datetime.now() + timedelta(minutes=1),
            replace_existing=True
        )
        
        # 恢复现有话题的定时任务
        session = db.get_session()
        try:
            active_topics = session.query(Topic).filter(Topic.is_active == True).all()
            for topic in active_topics:
                scheduler.add_topic_job(topic.id, topic.search_interval, search_topic_task)
        finally:
            session.close()
    
    try:
        # 修改为监听所有地址，以便通过本机IP访问
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=True)
    finally:
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
            scheduler.shutdown()