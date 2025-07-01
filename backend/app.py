from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import os
import json
import subprocess
import sys
from scheduler import TaskScheduler
from models import db, Script, ScriptRun
from templates import get_templates
import pytz

app = Flask(__name__)
CORS(app)

# 配置 - 将数据库位置修改到专门的 data 目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 在容器内，这将是 /app/data 目录
data_dir = os.path.join(project_root, 'data') 
# 确保目录存在
os.makedirs(data_dir, exist_ok=True) 
db_path = os.path.join(data_dir, 'scripts.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')

# 初始化数据库
db.init_app(app)

# 初始化调度器
scheduler = TaskScheduler()

# 静态文件路由
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

# API路由
@app.route('/api/scripts', methods=['GET'])
def get_scripts():
    """获取所有脚本"""
    scripts = Script.query.all()
    scripts_data = []
    for script in scripts:
        script_dict = script.to_dict()
        # 获取下次运行时间
        if script.is_active and script.cron_expression:
            next_run = scheduler.get_next_run_time(script.id)
            script_dict['next_run_time'] = next_run
        scripts_data.append(script_dict)
    return jsonify(scripts_data)

@app.route('/api/scripts', methods=['POST'])
def create_script():
    """创建新脚本"""
    data = request.json
    script = Script(
        name=data['name'],
        description=data.get('description', ''),
        code=data['code'],
        cron_expression=data.get('cron_expression', ''),
        is_active=data.get('is_active', False)
    )
    db.session.add(script)
    db.session.commit()
    
    if script.is_active and script.cron_expression:
        scheduler.add_job(script.id, script.cron_expression)
    
    return jsonify(script.to_dict()), 201

@app.route('/api/scripts/<int:script_id>', methods=['PUT'])
def update_script(script_id):
    """更新脚本"""
    script = Script.query.get_or_404(script_id)
    data = request.json
    
    # 如果调度状态改变，更新调度器
    old_active = script.is_active
    old_cron = script.cron_expression
    
    script.name = data.get('name', script.name)
    script.description = data.get('description', script.description)
    script.code = data.get('code', script.code)
    script.cron_expression = data.get('cron_expression', script.cron_expression)
    script.is_active = data.get('is_active', script.is_active)
    script.updated_at = datetime.now(timezone.utc)
    
    db.session.commit()
    
    # 更新调度器
    if old_active:
        scheduler.remove_job(script_id)
    
    if script.is_active and script.cron_expression:
        scheduler.add_job(script_id, script.cron_expression)
    
    # 获取更新后的数据，包括下次运行时间
    script_dict = script.to_dict()
    if script.is_active and script.cron_expression:
        next_run = scheduler.get_next_run_time(script.id)
        script_dict['next_run_time'] = next_run
    
    return jsonify(script_dict)

@app.route('/api/scripts/<int:script_id>', methods=['DELETE'])
def delete_script(script_id):
    """删除脚本"""
    script = Script.query.get_or_404(script_id)
    
    if script.is_active:
        scheduler.remove_job(script_id)
    
    db.session.delete(script)
    db.session.commit()
    return '', 204

@app.route('/api/scripts/<int:script_id>/run', methods=['POST'])
def run_script(script_id):
    """立即运行脚本"""
    script = Script.query.get_or_404(script_id)
    
    # 创建运行记录
    run = ScriptRun(script_id=script_id)
    db.session.add(run)
    db.session.commit()
    
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
        
    except subprocess.TimeoutExpired:
        run.error = "Script execution timeout"
        run.status = 'failed'
        run.completed_at = datetime.now(timezone.utc)
    except Exception as e:
        run.error = str(e)
        run.status = 'failed'
        run.completed_at = datetime.now(timezone.utc)
    
    db.session.commit()
    return jsonify(run.to_dict())

@app.route('/api/scripts/<int:script_id>/runs', methods=['GET'])
def get_script_runs(script_id):
    """获取脚本运行历史"""
    runs = ScriptRun.query.filter_by(script_id=script_id).order_by(ScriptRun.created_at.desc()).limit(20).all()
    return jsonify([run.to_dict() for run in runs])

@app.route('/api/templates', methods=['GET'])
def api_get_templates():
    """获取脚本模板"""
    return jsonify(get_templates())

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置信息"""
    config = {
        'database_location': os.path.abspath(db_path),
        'project_directory': os.path.dirname(os.path.abspath(__file__)),
        'environment_vars': {
            'GEMINI_API_KEY': '已设置' if os.environ.get('GEMINI_API_KEY') else '未设置',
            'BARK_DEVICE_KEY': '已设置' if os.environ.get('BARK_DEVICE_KEY') else '未设置',
            'BARK_API_SERVER': os.environ.get('BARK_API_SERVER', '未设置')
        }
    }
    return jsonify(config)

@app.route('/api/cron/parse', methods=['POST'])
def parse_cron():
    """解析cron表达式，返回描述"""
    data = request.json
    cron_expression = data.get('cron_expression', '').strip()
    
    if not cron_expression:
        return jsonify({'description': '未设置定时任务', 'valid': False})
    
    parts = cron_expression.split()
    if len(parts) != 5:
        return jsonify({'description': '无效的cron表达式，需要5个部分', 'valid': False})
    
    minute, hour, day, month, dow = parts
    
    # 生成描述
    descriptions = []
    
    # 分钟
    if minute == '*':
        descriptions.append('每分钟')
    elif '/' in minute:
        interval = minute.split('/')[1]
        descriptions.append(f'每{interval}分钟')
    elif ',' in minute:
        descriptions.append(f'在{minute}分')
    else:
        descriptions.append(f'在第{minute}分钟')
    
    # 小时
    if hour != '*':
        if ',' in hour:
            descriptions.append(f'的{hour}点')
        else:
            descriptions.append(f'的{hour}点')
    
    # 日期
    if day != '*':
        if ',' in day:
            descriptions.append(f'每月{day}日')
        else:
            descriptions.append(f'每月{day}日')
    
    # 月份
    if month != '*':
        if ',' in month:
            descriptions.append(f'在{month}月')
        else:
            descriptions.append(f'在{month}月')
    
    # 星期
    if dow != '*':
        dow_names = {
            '0': '周日', '1': '周一', '2': '周二', '3': '周三',
            '4': '周四', '5': '周五', '6': '周六', '7': '周日'
        }
        if ',' in dow:
            days = [dow_names.get(d, d) for d in dow.split(',')]
            descriptions.append(f'在{",".join(days)}')
        else:
            descriptions.append(f'在{dow_names.get(dow, dow)}')
    
    # 组合描述
    if minute == '0' and hour != '*' and day == '*' and month == '*' and dow == '*':
        description = f'每天{hour}点执行'
    elif minute != '*' and hour != '*' and day == '*' and month == '*' and dow == '*':
        description = f'每天{hour}:{minute.zfill(2)}执行'
    elif minute == '0' and hour == '0' and day != '*' and month == '*' and dow == '*':
        description = f'每月{day}日0点执行'
    elif dow != '*' and day == '*':
        dow_names = {
            '0': '周日', '1': '周一', '2': '周二', '3': '周三',
            '4': '周四', '5': '周五', '6': '周六', '7': '周日'
        }
        if ',' in dow:
            days = [dow_names.get(d, d) for d in dow.split(',')]
            description = f'每{",".join(days)}{hour}:{minute.zfill(2)}执行'
        else:
            description = f'每{dow_names.get(dow, dow)}{hour}:{minute.zfill(2)}执行'
    else:
        description = ' '.join(descriptions)
    
    # 尝试获取下次运行时间
    try:
        from apscheduler.triggers.cron import CronTrigger
        trigger = CronTrigger(
            minute=minute, hour=hour, day=day, month=month, day_of_week=dow,
            timezone='Asia/Shanghai'
        )
        next_time = trigger.get_next_fire_time(None, datetime.now(pytz.timezone('Asia/Shanghai')))
        if next_time:
            next_run = next_time.strftime('%Y-%m-%d %H:%M:%S')
            description += f'（下次运行：{next_run}）'
    except:
        pass
    
    return jsonify({'description': description, 'valid': True})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # 启动调度器
    scheduler.start()
    
    # 恢复已激活的定时任务
    with app.app_context():
        active_scripts = Script.query.filter_by(is_active=True).all()
        for script in active_scripts:
            if script.cron_expression:
                scheduler.add_job(script.id, script.cron_expression)
    
    # 打印配置信息
    print(f"\n{'='*50}")
    print("🚀 AI搜索与Bark推送管理系统已启动")
    print(f"{'='*50}")
    print(f"📁 数据库位置: {os.path.abspath(db_path)}")
    print(f"📂 项目目录: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"🌐 访问地址: http://localhost:5000")
    print(f"{'='*50}")
    print("环境变量状态:")
    print(f"  GEMINI_API_KEY: {'✅ 已设置' if os.environ.get('GEMINI_API_KEY') else '❌ 未设置'}")
    print(f"  BARK_DEVICE_KEY: {'✅ 已设置' if os.environ.get('BARK_DEVICE_KEY') else '❌ 未设置'}")
    print(f"  BARK_API_SERVER: {os.environ.get('BARK_API_SERVER', '使用默认服务器')}")
    print(f"{'='*50}\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)