"""
SillyTavern Python版本 - 提示词管理器
实现提示词集合管理和聊天完成功能
"""

import re
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class InjectionPosition(Enum):
    """注入位置枚举"""
    ABSOLUTE = "absolute"
    RELATIVE = "relative"


class PromptRole(Enum):
    """提示词角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Prompt:
    """提示词数据类"""
    identifier: str
    name: str
    content: str = ""
    role: PromptRole = PromptRole.SYSTEM
    system_prompt: bool = True
    marker: bool = False
    injection_position: InjectionPosition = InjectionPosition.RELATIVE
    injection_depth: int = 0
    injection_order: int = 0
    forbid_overrides: bool = False
    enabled: bool = True
    
    def __post_init__(self):
        if isinstance(self.role, str):
            self.role = PromptRole(self.role)
        if isinstance(self.injection_position, str):
            self.injection_position = InjectionPosition(self.injection_position)


@dataclass
class Message:
    """消息数据类"""
    name: str
    content: str
    role: PromptRole
    is_user: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.role, str):
            self.role = PromptRole(self.role)


@dataclass
class MessageCollection:
    """消息集合数据类"""
    source: str
    messages: List[Message] = field(default_factory=list)
    
    def add(self, message: Message):
        """添加消息"""
        self.messages.append(message)
    
    def get_content(self) -> str:
        """获取集合内容"""
        return "\n".join(msg.content for msg in self.messages if msg.content)


class PromptCollection:
    """提示词集合类"""
    
    def __init__(self):
        self.collection: List[Prompt] = []
        self.overridden_prompts: Dict[str, Prompt] = {}
    
    def add(self, prompt: Prompt):
        """添加提示词"""
        self.collection.append(prompt)
    
    def get(self, identifier: str) -> Optional[Prompt]:
        """获取提示词"""
        for prompt in self.collection:
            if prompt.identifier == identifier:
                return prompt
        return None
    
    def has(self, identifier: str) -> bool:
        """检查是否包含提示词"""
        return self.get(identifier) is not None
    
    def index(self, identifier: str) -> int:
        """获取提示词索引"""
        for i, prompt in enumerate(self.collection):
            if prompt.identifier == identifier:
                return i
        return -1
    
    def override(self, prompt: Prompt, index: int):
        """覆盖提示词"""
        if 0 <= index < len(self.collection):
            self.overridden_prompts[prompt.identifier] = self.collection[index]
            self.collection[index] = prompt


class ChatCompletion:
    """聊天完成类"""
    
    def __init__(self):
        self.collections: List[MessageCollection] = []
        self.token_budget: Optional[int] = None
        self.max_tokens: Optional[int] = None
        self.logging_enabled: bool = False
    
    def set_token_budget(self, max_context: int, max_tokens: int):
        """设置token预算"""
        self.token_budget = max_context
        self.max_tokens = max_tokens
    
    def reserve_budget(self, tokens: Union[int, MessageCollection]):
        """预留token预算"""
        if isinstance(tokens, int):
            if self.token_budget:
                self.token_budget -= tokens
        elif isinstance(tokens, MessageCollection):
            # 计算消息集合的token数量
            content = tokens.get_content()
            estimated_tokens = len(content.split()) * 1.3  # 简单估算
            if self.token_budget:
                self.token_budget -= int(estimated_tokens)
    
    def add(self, collection: MessageCollection, index: Optional[int] = None):
        """添加消息集合"""
        if index is not None:
            self.collections.insert(index, collection)
        else:
            self.collections.append(collection)
    
    def set_overridden_prompts(self, overridden_prompts: Dict[str, Prompt]):
        """设置被覆盖的提示词"""
        # 这里可以存储被覆盖的提示词信息
        pass
    
    def enable_logging(self):
        """启用日志"""
        self.logging_enabled = True
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """获取消息列表（用于API调用）"""
        messages = []
        
        for collection in self.collections:
            for message in collection.messages:
                messages.append({
                    'role': message.role.value,
                    'content': message.content,
                    'name': message.name if message.name else None
                })
        
        return messages


class PromptManager:
    """提示词管理器"""
    
    def __init__(self):
        self.active_character = None
        self.service_settings = {}
        self.prompts: Dict[str, Prompt] = {}
        self.character_prompts: Dict[str, Dict[str, Prompt]] = {}
        
        # 初始化默认提示词
        self._initialize_default_prompts()
    
    def _initialize_default_prompts(self):
        """初始化默认提示词"""
        default_prompts = [
            Prompt(
                identifier="main",
                name="Main Prompt",
                content="Write {{char}}'s next reply in a fictional chat between {{charIfNotGroup}} and {{user}}.",
                role=PromptRole.SYSTEM,
                system_prompt=True
            ),
            Prompt(
                identifier="nsfw",
                name="Auxiliary Prompt",
                content="",
                role=PromptRole.SYSTEM,
                system_prompt=True
            ),
            Prompt(
                identifier="dialogueExamples",
                name="Chat Examples",
                content="",
                role=PromptRole.SYSTEM,
                system_prompt=True,
                marker=True
            ),
            Prompt(
                identifier="jailbreak",
                name="Post-History Instructions",
                content="",
                role=PromptRole.SYSTEM,
                system_prompt=True
            ),
            Prompt(
                identifier="chatHistory",
                name="Chat History",
                content="",
                role=PromptRole.SYSTEM,
                system_prompt=True,
                marker=True
            ),
            Prompt(
                identifier="worldInfoAfter",
                name="World Info (after)",
                content="",
                role=PromptRole.SYSTEM,
                system_prompt=True,
                marker=True
            ),
            Prompt(
                identifier="worldInfoBefore",
                name="World Info (before)",
                content="",
                role=PromptRole.SYSTEM,
                system_prompt=True,
                marker=True
            ),
            Prompt(
                identifier="enhanceDefinitions",
                name="Enhance Definitions",
                content="If you have more knowledge of {{char}}, add to the character's lore and personality to enhance them but keep the Character Sheet's definitions absolute.",
                role=PromptRole.SYSTEM,
                system_prompt=True,
                marker=False
            ),
            Prompt(
                identifier="charDescription",
                name="Char Description",
                content="",
                role=PromptRole.SYSTEM,
                system_prompt=True,
                marker=True
            ),
            Prompt(
                identifier="charPersonality",
                name="Char Personality",
                content="",
                role=PromptRole.SYSTEM,
                system_prompt=True,
                marker=True
            ),
            Prompt(
                identifier="scenario",
                name="Scenario",
                content="",
                role=PromptRole.SYSTEM,
                system_prompt=True,
                marker=True
            ),
            Prompt(
                identifier="personaDescription",
                name="Persona Description",
                content="",
                role=PromptRole.SYSTEM,
                system_prompt=True,
                marker=True
            )
        ]
        
        for prompt in default_prompts:
            self.prompts[prompt.identifier] = prompt
    
    def get_prompt_by_id(self, identifier: str) -> Optional[Prompt]:
        """根据ID获取提示词"""
        return self.prompts.get(identifier)
    
    def get_prompt_order_for_character(self, character_id: Optional[str]) -> List[Dict[str, Any]]:
        """获取角色的提示词顺序"""
        # 简化实现，返回默认顺序
        order = []
        for prompt in self.prompts.values():
            order.append({
                'identifier': prompt.identifier,
                'enabled': prompt.enabled
            })
        return order
    
    def is_prompt_disabled_for_active_character(self, identifier: str) -> bool:
        """检查提示词是否对当前角色禁用"""
        if not self.active_character:
            return False
        
        # 检查角色特定的提示词设置
        character_prompts = self.character_prompts.get(self.active_character, {})
        if identifier in character_prompts:
            return not character_prompts[identifier].enabled
        
        return False
    
    def prepare_prompt(self, prompt: Prompt, original: Optional[str] = None) -> Prompt:
        """准备提示词"""
        prepared_prompt = Prompt(
            identifier=prompt.identifier,
            name=prompt.name,
            content=prompt.content,
            role=prompt.role,
            system_prompt=prompt.system_prompt,
            marker=prompt.marker,
            injection_position=prompt.injection_position,
            injection_depth=prompt.injection_depth,
            injection_order=prompt.injection_order,
            forbid_overrides=prompt.forbid_overrides,
            enabled=prompt.enabled
        )
        
        # 这里可以添加参数替换逻辑
        if original:
            prepared_prompt.content = prepared_prompt.content.replace("{{original}}", original)
        
        return prepared_prompt
    
    def get_prompt_collection(self) -> PromptCollection:
        """获取提示词集合"""
        prompt_order = self.get_prompt_order_for_character(self.active_character)
        
        prompt_collection = PromptCollection()
        
        for entry in prompt_order:
            if entry.get('enabled', True):
                prompt = self.get_prompt_by_id(entry['identifier'])
                if prompt:
                    prompt_collection.add(self.prepare_prompt(prompt))
            elif not entry.get('enabled') and entry['identifier'] == 'main':
                # 为扩展创建空的main提示词
                prompt = Prompt(
                    identifier='main',
                    name='Main Prompt',
                    content='',
                    role=PromptRole.SYSTEM,
                    system_prompt=True
                )
                prompt_collection.add(self.prepare_prompt(prompt))
        
        return prompt_collection
    
    def log(self, message: str):
        """记录日志"""
        logger.info(f"[PromptManager] {message}")


def format_world_info(world_info: str) -> str:
    """格式化世界信息"""
    if not world_info:
        return ""
    
    # 简单的格式化，可以添加更复杂的逻辑
    return world_info.strip()


def get_prompt_role(role: Union[str, int]) -> PromptRole:
    """获取提示词角色"""
    if isinstance(role, str):
        return PromptRole(role)
    elif isinstance(role, int):
        roles = [PromptRole.SYSTEM, PromptRole.USER, PromptRole.ASSISTANT]
        if 0 <= role < len(roles):
            return roles[role]
    return PromptRole.SYSTEM


def get_prompt_position(position: Union[str, int]) -> InjectionPosition:
    """获取提示词位置"""
    if isinstance(position, str):
        return InjectionPosition(position)
    elif isinstance(position, int):
        positions = [InjectionPosition.RELATIVE, InjectionPosition.ABSOLUTE]
        if 0 <= position < len(positions):
            return positions[position]
    return InjectionPosition.RELATIVE


async def prepare_prompts_for_chat_completion(params: Dict[str, Any]) -> PromptCollection:
    """为聊天完成准备提示词"""
    # 创建系统提示词
    system_prompts = [
        Prompt(
            identifier="worldInfoBefore",
            name="World Info (before)",
            content=format_world_info(params.get('worldInfoBefore', '')),
            role=PromptRole.SYSTEM,
            system_prompt=True,
            marker=True
        ),
        Prompt(
            identifier="worldInfoAfter",
            name="World Info (after)",
            content=format_world_info(params.get('worldInfoAfter', '')),
            role=PromptRole.SYSTEM,
            system_prompt=True,
            marker=True
        ),
        Prompt(
            identifier="charDescription",
            name="Char Description",
            content=params.get('charDescription', ''),
            role=PromptRole.SYSTEM,
            system_prompt=True,
            marker=True
        ),
        Prompt(
            identifier="charPersonality",
            name="Char Personality",
            content=params.get('charPersonality', ''),
            role=PromptRole.SYSTEM,
            system_prompt=True,
            marker=True
        ),
        Prompt(
            identifier="scenario",
            name="Scenario",
            content=params.get('scenario', ''),
            role=PromptRole.SYSTEM,
            system_prompt=True,
            marker=True
        ),
        Prompt(
            identifier="impersonate",
            name="Impersonation",
            content=params.get('impersonationPrompt', ''),
            role=PromptRole.SYSTEM,
            system_prompt=True,
            marker=False
        ),
        Prompt(
            identifier="quietPrompt",
            name="Quiet Prompt",
            content=params.get('quietPrompt', ''),
            role=PromptRole.SYSTEM,
            system_prompt=True,
            marker=False
        ),
        Prompt(
            identifier="groupNudge",
            name="Group Nudge",
            content=params.get('groupNudge', ''),
            role=PromptRole.SYSTEM,
            system_prompt=True,
            marker=False
        ),
        Prompt(
            identifier="bias",
            name="Bias",
            content=params.get('bias', ''),
            role=PromptRole.ASSISTANT,
            system_prompt=False,
            marker=False
        )
    ]
    
    # 处理扩展提示词
    extension_prompts = params.get('extensionPrompts', {})
    
    # 添加记忆摘要
    summary = extension_prompts.get('1_memory')
    if summary and summary.get('value'):
        system_prompts.append(Prompt(
            identifier="summary",
            name="Memory Summary",
            content=summary['value'],
            role=get_prompt_role(summary.get('role', 0)),
            system_prompt=True,
            marker=False
        ))
    
    # 添加作者注释
    authors_note = extension_prompts.get('2_floating_prompt')
    if authors_note and authors_note.get('value'):
        system_prompts.append(Prompt(
            identifier="authorsNote",
            name="Author's Note",
            content=authors_note['value'],
            role=get_prompt_role(authors_note.get('role', 0)),
            system_prompt=True,
            marker=False
        ))
    
    # 添加向量记忆
    vectors_memory = extension_prompts.get('3_vectors')
    if vectors_memory and vectors_memory.get('value'):
        system_prompts.append(Prompt(
            identifier="vectorsMemory",
            name="Vectors Memory",
            content=vectors_memory['value'],
            role=PromptRole.SYSTEM,
            system_prompt=True,
            marker=False
        ))
    
    # 创建提示词集合
    prompt_collection = PromptCollection()
    
    # 添加系统提示词
    for prompt in system_prompts:
        prompt_collection.add(prompt)
    
    return prompt_collection


async def populate_chat_completion(prompts: PromptCollection, chat_completion: ChatCompletion, 
                                 options: Dict[str, Any]):
    """填充聊天完成"""
    
    def add_to_chat_completion(source: str, target: Optional[str] = None):
        """添加到聊天完成"""
        if not prompts.has(source):
            return
        
        prompt = prompts.get(source)
        if not prompt:
            return
        
        if prompt.injection_position == InjectionPosition.ABSOLUTE:
            logger.info(f"Skipping prompt {source} because it is an absolute prompt")
            return
        
        index = prompts.index(target) if target else prompts.index(source)
        collection = MessageCollection(source)
        
        # 创建消息
        message = Message(
            name="",
            content=prompt.content,
            role=prompt.role,
            is_user=prompt.role == PromptRole.USER
        )
        
        collection.add(message)
        chat_completion.add(collection, index)
    
    # 预留预算
    chat_completion.reserve_budget(3)
    
    # 添加角色和世界信息
    await add_to_chat_completion('worldInfoBefore')
    await add_to_chat_completion('main')
    await add_to_chat_completion('worldInfoAfter')
    await add_to_chat_completion('charDescription')
    await add_to_chat_completion('charPersonality')
    await add_to_chat_completion('scenario')
    await add_to_chat_completion('personaDescription')
    
    # 设置被覆盖的提示词
    chat_completion.set_overridden_prompts(prompts.overridden_prompts)
    
    # 创建控制提示词集合
    control_prompts = MessageCollection('controlPrompts')
    
    # 添加静默提示词
    quiet_prompt = prompts.get('quietPrompt')
    if quiet_prompt and quiet_prompt.content:
        quiet_message = Message(
            name="",
            content=quiet_prompt.content,
            role=quiet_prompt.role,
            is_user=quiet_prompt.role == PromptRole.USER
        )
        control_prompts.add(quiet_message)
    
    # 预留控制提示词预算
    chat_completion.reserve_budget(control_prompts)
    
    # 添加系统提示词
    system_prompts = ['nsfw', 'jailbreak']
    for prompt_id in system_prompts:
        await add_to_chat_completion(prompt_id)
    
    # 添加用户相对提示词
    user_relative_prompts = []
    for prompt in prompts.collection:
        if not prompt.system_prompt and prompt.injection_position != InjectionPosition.ABSOLUTE:
            user_relative_prompts.append(prompt.identifier)
    
    for prompt_id in user_relative_prompts:
        await add_to_chat_completion(prompt_id)


async def prepare_openai_messages(params: Dict[str, Any], dry_run: bool = False) -> Tuple[List[Dict[str, Any]], bool]:
    """准备OpenAI消息"""
    # 创建聊天完成实例
    chat_completion = ChatCompletion()
    
    # 设置token预算
    chat_completion.set_token_budget(
        params.get('openai_max_context', 4096),
        params.get('openai_max_tokens', 2048)
    )
    
    try:
        # 准备提示词
        prompts = await prepare_prompts_for_chat_completion(params)
        
        # 填充聊天完成
        await populate_chat_completion(prompts, chat_completion, params)
        
        # 获取消息
        messages = chat_completion.get_messages()
        
        return messages, True
        
    except Exception as e:
        logger.error(f"准备OpenAI消息时出错: {e}")
        return [], False


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def test_prompt_manager():
        # 创建提示词管理器
        prompt_manager = PromptManager()
        
        # 设置服务设置
        prompt_manager.service_settings = {
            'openai_max_context': 4096,
            'openai_max_tokens': 2048
        }
        
        # 测试参数
        test_params = {
            'charDescription': 'A helpful AI assistant',
            'charPersonality': 'Friendly and knowledgeable',
            'scenario': 'You are chatting with an AI assistant',
            'worldInfoBefore': 'This is a virtual chat room',
            'worldInfoAfter': 'The conversation continues',
            'quietPrompt': 'Please be helpful',
            'bias': 'Always be polite',
            'extensionPrompts': {
                '1_memory': {'value': 'Previous conversation summary', 'role': 0},
                '2_floating_prompt': {'value': 'Author note', 'role': 0}
            }
        }
        
        # 准备OpenAI消息
        messages, success = await prepare_openai_messages(test_params)
        
        if success:
            print("准备的消息:")
            for i, message in enumerate(messages):
                print(f"{i+1}. Role: {message['role']}, Content: {message['content'][:50]}...")
        else:
            print("准备消息失败")
    
    # 运行测试
    asyncio.run(test_prompt_manager()) 