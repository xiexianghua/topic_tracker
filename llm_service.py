from google import genai
from google.genai import types
import logging
import gc

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, api_key):
        self.api_key = api_key
        # 不在初始化时创建client，减少内存占用
        self._client = None
        self._grounding_tool = None
    
    @property
    def client(self):
        """延迟加载client"""
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client
    
    @property
    def grounding_tool(self):
        """延迟加载grounding tool"""
        if self._grounding_tool is None:
            self._grounding_tool = types.Tool(
                google_search=types.GoogleSearch()
            )
        return self._grounding_tool
    
    def search_topic(self, query):
        """执行话题搜索"""
        try:
            config = types.GenerateContentConfig(
                tools=[self.grounding_tool]
            )
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",  # 使用更新的模型
                contents=f"{query} 不包含其他格式，纯文本回答。",
                config=config,
            )
            
            result = response.text
            
            # 清理response对象，释放内存
            del response
            gc.collect()
            
            return result
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            return None
    
    def __del__(self):
        """清理资源"""
        if self._client:
            del self._client
        if self._grounding_tool:
            del self._grounding_tool