"""
SillyTavern Python版本 - 聊天后端系统
实现多API适配和消息生成功能
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import re

from character_system import CharacterSystem, StoryStringParams
from prompt_manager import ChatCompletion, MessageCollection, Message, PromptRole

logger = logging.getLogger(__name__)


class ChatCompletionSource(Enum):
    """聊天完成源枚举"""
    OPENAI = "openai"
    CLAUDE = "claude"
    MISTRALAI = "mistralai"
    COHERE = "cohere"
    DEEPSEEK = "deepseek"
    XAI = "xai"
    CUSTOM = "custom"


class TextCompletionModels(Enum):
    """文本完成模型枚举"""
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    MISTRAL_LARGE = "mistral-large-latest"


@dataclass
class GenerationRequest:
    """生成请求数据类"""
    messages: List[Dict[str, Any]]
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    top_k: Optional[int] = None
    stop: Optional[List[str]] = None
    stream: bool = False
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    seed: Optional[int] = None
    logit_bias: Optional[Dict[str, float]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    chat_completion_source: ChatCompletionSource = ChatCompletionSource.OPENAI


class ChatBackend:
    """聊天后端核心类"""
    
    def __init__(self):
        self.character_system = CharacterSystem()
        self.api_keys = {}
        self.api_urls = {
            ChatCompletionSource.OPENAI: "https://api.openai.com/v1",
            ChatCompletionSource.CLAUDE: "https://api.anthropic.com",
            ChatCompletionSource.MISTRALAI: "https://api.mistral.ai/v1",
            ChatCompletionSource.COHERE: "https://api.cohere.ai/v1",
            ChatCompletionSource.DEEPSEEK: "https://api.deepseek.com/v1",
            ChatCompletionSource.XAI: "https://api.x.ai/v1",
        }
        self.session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    def set_api_key(self, source: ChatCompletionSource, api_key: str):
        """设置API密钥"""
        self.api_keys[source] = api_key
    
    def set_api_url(self, source: ChatCompletionSource, url: str):
        """设置API URL"""
        self.api_urls[source] = url
    
    async def generate(self, request: GenerationRequest) -> Dict[str, Any]:
        """
        生成回复
        
        Args:
            request: 生成请求
            
        Returns:
            Dict[str, Any]: 生成结果
        """
        try:
            if request.chat_completion_source == ChatCompletionSource.CLAUDE:
                return await self._send_claude_request(request)
            elif request.chat_completion_source == ChatCompletionSource.MISTRALAI:
                return await self._send_mistralai_request(request)
            elif request.chat_completion_source == ChatCompletionSource.COHERE:
                return await self._send_cohere_request(request)
            elif request.chat_completion_source == ChatCompletionSource.DEEPSEEK:
                return await self._send_deepseek_request(request)
            elif request.chat_completion_source == ChatCompletionSource.XAI:
                return await self._send_xai_request(request)
            else:
                return await self._send_openai_request(request)
                
        except Exception as e:
            logger.error(f"生成回复时出错: {e}")
            return {"error": True, "message": str(e)}
    
    async def _send_openai_request(self, request: GenerationRequest) -> Dict[str, Any]:
        """发送OpenAI请求"""
        api_key = self.api_keys.get(ChatCompletionSource.OPENAI)
        if not api_key:
            return {"error": True, "message": "OpenAI API key is missing"}
        
        url = f"{self.api_urls[ChatCompletionSource.OPENAI]}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        body = {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stream": request.stream,
            "presence_penalty": request.presence_penalty,
            "frequency_penalty": request.frequency_penalty,
        }
        
        if request.top_k:
            body["top_k"] = request.top_k
        
        if request.stop:
            body["stop"] = request.stop
        
        if request.seed:
            body["seed"] = request.seed
        
        if request.logit_bias:
            body["logit_bias"] = request.logit_bias
        
        if request.tools:
            body["tools"] = request.tools
            body["tool_choice"] = request.tool_choice or "auto"
        
        async with self.session.post(url, headers=headers, json=body) as response:
            if response.status == 200:
                result = await response.json()
                return result
            else:
                error_text = await response.text()
                logger.error(f"OpenAI API error: {response.status} {error_text}")
                return {"error": True, "message": error_text}
    
    async def _send_claude_request(self, request: GenerationRequest) -> Dict[str, Any]:
        """发送Claude请求"""
        api_key = self.api_keys.get(ChatCompletionSource.CLAUDE)
        if not api_key:
            return {"error": True, "message": "Claude API key is missing"}
        
        url = f"{self.api_urls[ChatCompletionSource.CLAUDE]}/v1/messages"
        
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        # 转换消息格式
        converted_messages = self._convert_claude_messages(request.messages)
        
        body = {
            "model": request.model,
            "messages": converted_messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "stream": request.stream,
        }
        
        if request.stop:
            body["stop_sequences"] = request.stop
        
        if request.tools:
            body["tools"] = request.tools
            body["tool_choice"] = request.tool_choice or "auto"
        
        async with self.session.post(url, headers=headers, json=body) as response:
            if response.status == 200:
                result = await response.json()
                return result
            else:
                error_text = await response.text()
                logger.error(f"Claude API error: {response.status} {error_text}")
                return {"error": True, "message": error_text}
    
    async def _send_mistralai_request(self, request: GenerationRequest) -> Dict[str, Any]:
        """发送MistralAI请求"""
        api_key = self.api_keys.get(ChatCompletionSource.MISTRALAI)
        if not api_key:
            return {"error": True, "message": "MistralAI API key is missing"}
        
        url = f"{self.api_urls[ChatCompletionSource.MISTRALAI]}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        body = {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stream": request.stream,
            "presence_penalty": request.presence_penalty,
            "frequency_penalty": request.frequency_penalty,
        }
        
        if request.stop:
            body["stop"] = request.stop
        
        if request.seed:
            body["seed"] = request.seed
        
        async with self.session.post(url, headers=headers, json=body) as response:
            if response.status == 200:
                result = await response.json()
                return result
            else:
                error_text = await response.text()
                logger.error(f"MistralAI API error: {response.status} {error_text}")
                return {"error": True, "message": error_text}
    
    async def _send_cohere_request(self, request: GenerationRequest) -> Dict[str, Any]:
        """发送Cohere请求"""
        api_key = self.api_keys.get(ChatCompletionSource.COHERE)
        if not api_key:
            return {"error": True, "message": "Cohere API key is missing"}
        
        url = f"{self.api_urls[ChatCompletionSource.COHERE]}/chat"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        body = {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "p": request.top_p,
            "stream": request.stream,
            "presence_penalty": request.presence_penalty,
            "frequency_penalty": request.frequency_penalty,
        }
        
        if request.stop:
            body["stop_sequences"] = request.stop
        
        if request.seed:
            body["seed"] = request.seed
        
        if request.tools:
            body["tools"] = request.tools
        
        async with self.session.post(url, headers=headers, json=body) as response:
            if response.status == 200:
                result = await response.json()
                return result
            else:
                error_text = await response.text()
                logger.error(f"Cohere API error: {response.status} {error_text}")
                return {"error": True, "message": error_text}
    
    async def _send_deepseek_request(self, request: GenerationRequest) -> Dict[str, Any]:
        """发送DeepSeek请求"""
        api_key = self.api_keys.get(ChatCompletionSource.DEEPSEEK)
        if not api_key:
            return {"error": True, "message": "DeepSeek API key is missing"}
        
        url = f"{self.api_urls[ChatCompletionSource.DEEPSEEK]}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        body = {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stream": request.stream,
            "presence_penalty": request.presence_penalty,
            "frequency_penalty": request.frequency_penalty,
        }
        
        if request.stop:
            body["stop"] = request.stop
        
        if request.seed:
            body["seed"] = request.seed
        
        async with self.session.post(url, headers=headers, json=body) as response:
            if response.status == 200:
                result = await response.json()
                return result
            else:
                error_text = await response.text()
                logger.error(f"DeepSeek API error: {response.status} {error_text}")
                return {"error": True, "message": error_text}
    
    async def _send_xai_request(self, request: GenerationRequest) -> Dict[str, Any]:
        """发送xAI请求"""
        api_key = self.api_keys.get(ChatCompletionSource.XAI)
        if not api_key:
            return {"error": True, "message": "xAI API key is missing"}
        
        url = f"{self.api_urls[ChatCompletionSource.XAI]}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        body = {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stream": request.stream,
            "presence_penalty": request.presence_penalty,
            "frequency_penalty": request.frequency_penalty,
        }
        
        if request.stop:
            body["stop"] = request.stop
        
        if request.seed:
            body["seed"] = request.seed
        
        async with self.session.post(url, headers=headers, json=body) as response:
            if response.status == 200:
                result = await response.json()
                return result
            else:
                error_text = await response.text()
                logger.error(f"xAI API error: {response.status} {error_text}")
                return {"error": True, "message": error_text}
    
    def _convert_claude_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换Claude消息格式"""
        converted = []
        
        for message in messages:
            converted_message = {
                "role": message["role"],
                "content": message["content"]
            }
            
            # 处理工具调用
            if "tool_calls" in message:
                converted_message["tool_calls"] = message["tool_calls"]
            
            # 处理工具结果
            if "tool_call_id" in message:
                converted_message["tool_call_id"] = message["tool_call_id"]
            
            converted.append(converted_message)
        
        return converted
    
    async def generate_with_character_context(self, user_message: str, 
                                            character_id: Optional[int] = None,
                                            chat_history: Optional[List[Dict[str, Any]]] = None,
                                            source: ChatCompletionSource = ChatCompletionSource.OPENAI,
                                            model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        """
        使用角色上下文生成回复
        
        Args:
            user_message: 用户消息
            character_id: 角色ID
            chat_history: 聊天历史
            source: API源
            model: 模型名称
            
        Returns:
            Dict[str, Any]: 生成结果
        """
        # 设置当前角色
        if character_id is not None:
            self.character_system.current_character_id = character_id
        
        # 获取角色卡片字段
        fields = self.character_system.get_character_card_fields()
        
        # 创建故事字符串参数
        story_params = StoryStringParams(
            description=fields.description,
            personality=fields.personality,
            scenario=fields.scenario,
            system=fields.system,
            char=self.character_system.name2,
            user=self.character_system.name1,
            mes_examples=fields.mes_examples
        )
        
        # 渲染故事字符串
        story_string = self.character_system.render_story_string(story_params)
        
        # 构建消息列表
        messages = []
        
        # 添加系统消息（故事字符串）
        if story_string.strip():
            messages.append({
                "role": "system",
                "content": story_string.strip()
            })
        
        # 添加聊天历史
        if chat_history:
            messages.extend(chat_history)
        
        # 添加用户消息
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # 创建生成请求
        request = GenerationRequest(
            messages=messages,
            model=model,
            chat_completion_source=source,
            temperature=0.7,
            max_tokens=2048
        )
        
        # 生成回复
        return await self.generate(request)


# 使用示例
async def main():
    async with ChatBackend() as backend:
        # 设置API密钥
        backend.set_api_key(ChatCompletionSource.OPENAI, "your-openai-api-key")
        
        # 添加示例角色
        backend.character_system.characters.append({
            'name': 'Alice',
            'description': 'A friendly AI assistant who loves to help users.',
            'personality': 'Alice is cheerful, helpful, and always eager to assist.',
            'scenario': 'You are chatting with Alice in a cozy virtual room.',
            'mes_example': '{{user}}: Hello Alice!\n{{char}}: Hi there! How can I help you today?',
            'data': {
                'system_prompt': 'You are Alice, a helpful AI assistant.',
                'post_history_instructions': 'Always be helpful and friendly.',
                'character_version': '1.0',
                'creator_notes': 'Created as a helpful assistant character.'
            }
        })
        
        backend.character_system.current_character_id = 0
        backend.character_system.name1 = "User"
        backend.character_system.name2 = "Alice"
        
        # 生成回复
        result = await backend.generate_with_character_context(
            user_message="Hello Alice! How are you today?",
            source=ChatCompletionSource.OPENAI,
            model="gpt-3.5-turbo"
        )
        
        print("生成结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main()) 