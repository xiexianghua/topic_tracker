from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import pytz

class RSSGenerator:
    def __init__(self, title, description, link):
        self.title = title
        self.description = description
        self.link = link
        self.beijing_tz = pytz.timezone('Asia/Shanghai')
    
    def generate_feed(self, items):
        """生成RSS feed"""
        fg = FeedGenerator()
        fg.title(self.title)
        fg.description(self.description)
        fg.link(href=self.link, rel='alternate')
        fg.language('zh')
        
        # 重要：确保items按时间降序排序（最新的在前）
        sorted_items = sorted(items, key=lambda x: x['created_at'], reverse=True)
        
        # feedgen会把后添加的条目放在RSS的前面，所以我们需要反转顺序
        # 这样最新的条目会最后添加，从而出现在RSS的最前面
        for item in reversed(sorted_items):
            fe = fg.add_entry()
            # 确保时间有时区信息
            if item['created_at'].tzinfo is None:
                item['created_at'] = item['created_at'].replace(tzinfo=timezone.utc)
            # 转换为北京时间显示
            beijing_time = item['created_at'].astimezone(self.beijing_tz)
            fe.title(f"{item['topic_name']} - {beijing_time.strftime('%Y-%m-%d %H:%M:%S')} 北京时间")
            fe.description(item['content'])
            fe.link(href=f"{self.link}/result/{item['id']}")
            # RSS标准要求使用UTC时间，但我们在标题中显示北京时间
            fe.pubDate(item['created_at'])
            fe.guid(str(item['id']), permalink=True)
        
        return fg.rss_str(pretty=True)