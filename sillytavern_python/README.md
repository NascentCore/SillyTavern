# SillyTavern Python 版本

这是 SillyTavern 的 Python 重写版本，实现了角色卡片信息插入机制和聊天后端系统。

## 功能特性

### 1. 角色卡片系统 (`character_system.py`)

- **角色卡片字段提取**: 从角色数据中提取描述、性格、场景等信息
- **故事字符串渲染**: 使用 Handlebars 风格的模板引擎渲染角色信息
- **参数替换系统**: 动态替换用户名称、角色名称等变量
- **扩展提示词管理**: 支持分层注入和角色特定的提示词

### 2. 提示词管理器 (`prompt_manager.py`)

- **提示词集合管理**: 管理不同类型的提示词（系统、用户、助手）
- **聊天完成功能**: 构建符合 API 要求的消息格式
- **Token 预算管理**: 智能管理上下文长度和生成 token 数量
- **多角色支持**: 支持群组角色和角色特定的提示词设置

### 3. 聊天后端系统 (`chat_backend.py`)

- **多 API 适配**: 支持 OpenAI、Claude、MistralAI、Cohere、DeepSeek、xAI 等
- **异步处理**: 使用 aiohttp 进行高效的异步 HTTP 请求
- **统一接口**: 提供统一的生成接口，简化 API 调用
- **错误处理**: 完善的错误处理和日志记录

## 安装和设置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 环境变量配置

创建 `.env` 文件：

```env
# API密钥
OPENAI_API_KEY=your-openai-api-key
CLAUDE_API_KEY=your-claude-api-key
MISTRALAI_API_KEY=your-mistralai-api-key
COHERE_API_KEY=your-cohere-api-key
DEEPSEEK_API_KEY=your-deepseek-api-key
XAI_API_KEY=your-xai-api-key

# 配置
LOG_LEVEL=INFO
DEFAULT_MODEL=gpt-3.5-turbo
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=2048
```

## 使用示例

### 基本使用

```python
import asyncio
from chat_backend import ChatBackend, ChatCompletionSource
from character_system import CharacterSystem

async def main():
    async with ChatBackend() as backend:
        # 设置API密钥
        backend.set_api_key(ChatCompletionSource.OPENAI, "your-api-key")

        # 添加角色
        backend.character_system.characters.append({
            'name': 'Alice',
            'description': 'A friendly AI assistant.',
            'personality': 'Cheerful and helpful.',
            'scenario': 'You are chatting with Alice.',
            'data': {
                'system_prompt': 'You are Alice, a helpful assistant.',
                'post_history_instructions': 'Always be helpful.'
            }
        })

        # 设置当前角色
        backend.character_system.current_character_id = 0
        backend.character_system.name1 = "User"
        backend.character_system.name2 = "Alice"

        # 生成回复
        result = await backend.generate_with_character_context(
            user_message="Hello Alice!",
            source=ChatCompletionSource.OPENAI,
            model="gpt-3.5-turbo"
        )

        print(result)

asyncio.run(main())
```

### 高级使用

```python
from character_system import CharacterSystem, StoryStringParams
from prompt_manager import PromptManager, ChatCompletion

# 角色系统使用
character_system = CharacterSystem()

# 获取角色卡片字段
fields = character_system.get_character_card_fields()

# 创建故事字符串参数
story_params = StoryStringParams(
    description=fields.description,
    personality=fields.personality,
    scenario=fields.scenario,
    char="Alice",
    user="User"
)

# 渲染故事字符串
story_string = character_system.render_story_string(story_params)
print(story_string)

# 提示词管理器使用
prompt_manager = PromptManager()
prompt_collection = prompt_manager.get_prompt_collection()

# 聊天完成
chat_completion = ChatCompletion()
chat_completion.set_token_budget(4096, 2048)
```

## 核心设计模式

### 1. 模板引擎模式

```python
# 故事字符串模板
template = """
{{#if system}}{{system}}
{{/if}}{{#if description}}{{description}}
{{/if}}{{#if personality}}{{personality}}
{{/if}}{{#if scenario}}{{scenario}}
{{/if}}
"""

# 参数替换
params = StoryStringParams(
    description="A helpful AI assistant",
    personality="Friendly and knowledgeable",
    scenario="Virtual chat room"
)
```

### 2. 分层注入模式

```python
# 扩展提示词注入
character_system.set_extension_prompt(
    key="memory",
    value="Previous conversation summary",
    position=1,  # IN_PROMPT
    depth=0,
    role=ExtensionPromptRoles.SYSTEM
)
```

### 3. 多 API 适配模式

```python
# 统一的生成接口
request = GenerationRequest(
    messages=messages,
    model="gpt-3.5-turbo",
    chat_completion_source=ChatCompletionSource.OPENAI,
    temperature=0.7,
    max_tokens=2048
)

result = await backend.generate(request)
```

## 架构设计

### 系统架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Character     │    │   Prompt        │    │   Chat          │
│   System        │    │   Manager       │    │   Backend       │
│                 │    │                 │    │                 │
│ • 角色卡片提取   │    │ • 提示词集合    │    │ • 多API适配     │
│ • 故事字符串渲染 │    │ • Token预算管理 │    │ • 异步HTTP请求  │
│ • 参数替换      │    │ • 消息格式化    │    │ • 错误处理      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Generation    │
                    │   Request       │
                    │                 │
                    │ • 统一请求格式   │
                    │ • 角色上下文     │
                    │ • 聊天历史       │
                    └─────────────────┘
```

### 数据流

1. **角色信息提取**: 从角色卡片中提取描述、性格等信息
2. **故事字符串渲染**: 使用模板引擎渲染角色信息
3. **提示词组装**: 将角色信息、聊天历史、扩展提示词组装
4. **API 调用**: 根据选择的 API 源发送请求
5. **响应处理**: 处理 API 响应并返回结果

## 扩展开发

### 添加新的 API 支持

```python
class ChatCompletionSource(Enum):
    NEW_API = "new_api"

class ChatBackend:
    async def _send_new_api_request(self, request: GenerationRequest) -> Dict[str, Any]:
        # 实现新的API请求逻辑
        pass
```

### 添加新的提示词类型

```python
@dataclass
class CustomPrompt(Prompt):
    custom_field: str = ""

# 在PromptManager中注册
prompt_manager.prompts["custom"] = CustomPrompt(...)
```

## 测试

运行测试：

```bash
pytest tests/
```

运行特定测试：

```bash
pytest tests/test_character_system.py -v
```

## 贡献

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 致谢

感谢原 SillyTavern 项目的开发者们，这个 Python 版本是基于原 JavaScript 版本的架构设计重写的。
