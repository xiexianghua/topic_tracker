import os
from google import genai
from google.genai import types
import logging

logger = logging.getLogger(__name__)

class AISearcher:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
        self.client = genai.Client(api_key=self.api_key)
        self.grounding_tool = types.Tool(google_search=types.GoogleSearch())
        self.config = types.GenerateContentConfig(tools=[self.grounding_tool])
    
    def search(self, query, model="gemini-2.5-flash"):
        """执行AI搜索"""
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=query,
                config=self.config,
            )
            return response.text
        except Exception as e:
            logger.error(f"AI搜索失败: {e}")
            return None

# 使用示例
if __name__ == "__main__":
    searcher = AISearcher()
    result = searcher.search("今天的科技新闻")
    print(result)