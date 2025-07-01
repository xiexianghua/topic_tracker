"""
脚本模板定义
"""

def get_templates():
    """获取所有脚本模板"""
    return [
        {
            'name': 'AI搜索并推送',
            'description': '使用Google Gemini搜索信息并通过Bark推送',
            'code': '''import os
from google import genai
from google.genai import types
from bark_sender import send_bark_notification

# 配置 - 请替换为你的实际密钥
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'YOUR_API_KEY')
BARK_DEVICE_KEY = os.environ.get('BARK_DEVICE_KEY', 'YOUR_BARK_KEY')

# 配置Gemini客户端
client = genai.Client(api_key=GEMINI_API_KEY)
grounding_tool = types.Tool(google_search=types.GoogleSearch())
config = types.GenerateContentConfig(tools=[grounding_tool])

# 搜索查询
query = "今天关于人工智能的最新新闻"

try:
    # 执行搜索
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=query,
        config=config,
    )
    
    # 发送Bark通知
    if response.text:
        success, result = send_bark_notification(
            device_key=BARK_DEVICE_KEY,
            title=f"AI搜索: {query[:20]}...",
            body=response.text[:1000],  # 限制长度
            group="AI搜索"
        )
        print(f"推送{'成功' if success else '失败'}: {result}")
        print(f"搜索结果: {response.text[:1000]}...")
    else:
        print("没有获取到搜索结果")
except Exception as e:
    print(f"执行出错: {str(e)}")
'''
        },
        {
            'name': '定时天气推送',
            'description': '搜索天气信息并推送',
            'code': '''import os
from google import genai
from google.genai import types
from bark_sender import send_bark_notification
from datetime import datetime

# 配置
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'YOUR_API_KEY')
BARK_DEVICE_KEY = os.environ.get('BARK_DEVICE_KEY', 'YOUR_BARK_KEY')

# 配置Gemini
client = genai.Client(api_key=GEMINI_API_KEY)
grounding_tool = types.Tool(google_search=types.GoogleSearch())
config = types.GenerateContentConfig(tools=[grounding_tool])

# 获取天气信息
city = "台北"
query = f"{city}今天的天气预报，包括温度、天气状况和建议"

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=query,
        config=config,
    )
    
    # 推送天气信息
    if response.text:
        current_time = datetime.now().strftime("%H:%M")
        success, result = send_bark_notification(
            device_key=BARK_DEVICE_KEY,
            title=f"🌤️ {city}天气 - {current_time}",
            body=response.text,
            sound="glass",
            group="天气预报"
        )
        print(f"天气推送{'成功' if success else '失败'}")
        print(f"天气信息: {response.text}")
except Exception as e:
    print(f"获取天气失败: {str(e)}")
'''
        },
        {
            'name': '股票价格监控',
            'description': '监控特定股票价格并推送',
            'code': '''import os
from google import genai
from google.genai import types
from bark_sender import send_bark_notification

# 配置
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'YOUR_API_KEY')
BARK_DEVICE_KEY = os.environ.get('BARK_DEVICE_KEY', 'YOUR_BARK_KEY')

# 配置Gemini
client = genai.Client(api_key=GEMINI_API_KEY)
grounding_tool = types.Tool(google_search=types.GoogleSearch())
config = types.GenerateContentConfig(tools=[grounding_tool])

# 股票列表
stocks = ["AAPL", "GOOGL", "TSLA"]

for stock in stocks:
    query = f"{stock}股票今日价格和涨跌幅"
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=config,
        )
        
        if response.text:
            # 根据内容判断是否需要推送（可以添加条件）
            success, result = send_bark_notification(
                device_key=BARK_DEVICE_KEY,
                title=f"📈 {stock} 股票信息",
                body=response.text,
                group="股票监控"
            )
            print(f"{stock} 推送结果: {'成功' if success else '失败'}")
            print(f"{stock} 信息: {response.text[:200]}...")
    except Exception as e:
        print(f"获取{stock}股票信息失败: {str(e)}")
'''
        },
        {
            'name': '简单测试脚本',
            'description': '测试脚本运行环境',
            'code': '''import os
import sys
from datetime import datetime

print(f"脚本开始运行: {datetime.now()}")
print(f"Python版本: {sys.version}")
print(f"当前目录: {os.getcwd()}")
print(f"Python路径: {sys.path[:3]}...")

# 测试导入项目模块
try:
    from bark_sender import send_bark_notification
    print("✅ 成功导入 bark_sender 模块")
except ImportError as e:
    print(f"❌ 导入 bark_sender 失败: {e}")

try:
    from ai_search import AISearcher
    print("✅ 成功导入 ai_search 模块")
except ImportError as e:
    print(f"❌ 导入 ai_search 失败: {e}")

# 测试环境变量
print(f"\\nGEMINI_API_KEY 已设置: {'是' if os.environ.get('GEMINI_API_KEY') else '否'}")
print(f"BARK_DEVICE_KEY 已设置: {'是' if os.environ.get('BARK_DEVICE_KEY') else '否'}")
print(f"BARK_API_SERVER: {os.environ.get('BARK_API_SERVER', '未设置')}")

print(f"\\n脚本运行完成: {datetime.now()}")
'''
        },
        {
            'name': '新闻摘要推送',
            'description': '获取特定主题的新闻摘要并推送',
            'code': '''import os
from google import genai
from google.genai import types
from bark_sender import send_bark_notification
from datetime import datetime

# 配置
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'YOUR_API_KEY')
BARK_DEVICE_KEY = os.environ.get('BARK_DEVICE_KEY', 'YOUR_BARK_KEY')

# 配置Gemini
client = genai.Client(api_key=GEMINI_API_KEY)
grounding_tool = types.Tool(google_search=types.GoogleSearch())
config = types.GenerateContentConfig(tools=[grounding_tool])

# 新闻主题列表
topics = ["人工智能", "新能源汽车", "半导体"]

for topic in topics:
    query = f"今天关于{topic}的最新新闻，请提供3-5条重要新闻的摘要"
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=config,
        )
        
        if response.text:
            success, result = send_bark_notification(
                device_key=BARK_DEVICE_KEY,
                title=f"📰 {topic}新闻摘要",
                body=response.text[:1000],  # 限制长度
                group="新闻摘要",
                level="timeSensitive"  # iOS 15+ 时效性通知
            )
            print(f"{topic} 新闻推送{'成功' if success else '失败'}")
            print("-" * 50)
            print(f"{topic} 新闻内容:\\n{response.text}")
            print("-" * 50)
    except Exception as e:
        print(f"获取{topic}新闻失败: {str(e)}")
'''
        },
        {
            'name': '汇率监控',
            'description': '监控汇率变化并推送',
            'code': '''import os
from google import genai
from google.genai import types
from bark_sender import send_bark_notification

# 配置
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'YOUR_API_KEY')
BARK_DEVICE_KEY = os.environ.get('BARK_DEVICE_KEY', 'YOUR_BARK_KEY')

# 配置Gemini
client = genai.Client(api_key=GEMINI_API_KEY)
grounding_tool = types.Tool(google_search=types.GoogleSearch())
config = types.GenerateContentConfig(tools=[grounding_tool])

# 监控的汇率对
currency_pairs = ["USD/CNY", "EUR/USD", "BTC/USD"]

for pair in currency_pairs:
    query = f"{pair}当前汇率和今日涨跌幅"
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=config,
        )
        
        if response.text:
            success, result = send_bark_notification(
                device_key=BARK_DEVICE_KEY,
                title=f"💱 {pair} 汇率",
                body=response.text,
                group="汇率监控",
                sound="minuet"
            )
            print(f"{pair} 汇率推送{'成功' if success else '失败'}")
            print(f"{pair}: {response.text}")
    except Exception as e:
        print(f"获取{pair}汇率失败: {str(e)}")
'''
        }
    ]