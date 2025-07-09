"""
SillyTavern Python版本 - 角色卡片系统
实现角色卡片信息提取、故事字符串渲染和提示词组装功能
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PersonaDescriptionPosition(Enum):
    """用户人设描述位置枚举"""
    IN_PROMPT = "in_prompt"
    IN_CHAT = "in_chat"


class ExtensionPromptTypes(Enum):
    """扩展提示词类型枚举"""
    BEFORE_PROMPT = "before_prompt"
    IN_PROMPT = "in_prompt"
    IN_CHAT = "in_chat"


class ExtensionPromptRoles(Enum):
    """扩展提示词角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class CharacterCardFields:
    """角色卡片字段数据类"""
    system: str = ""
    mes_examples: str = ""
    description: str = ""
    personality: str = ""
    persona: str = ""
    scenario: str = ""
    jailbreak: str = ""
    version: str = ""
    char_depth_prompt: str = ""
    creator_notes: str = ""


@dataclass
class StoryStringParams:
    """故事字符串参数数据类"""
    description: str = ""
    personality: str = ""
    persona: str = ""
    scenario: str = ""
    system: str = ""
    char: str = ""
    user: str = ""
    wi_before: str = ""
    wi_after: str = ""
    lore_before: str = ""
    lore_after: str = ""
    mes_examples: str = ""
    mes_examples_raw: str = ""


class CharacterSystem:
    """角色系统核心类"""
    
    def __init__(self):
        self.characters = []
        self.current_character_id = None
        self.selected_group = None
        self.name1 = "You"  # 用户名
        self.name2 = "Assistant"  # 角色名
        self.power_user_settings = {
            "persona_description_position": PersonaDescriptionPosition.IN_PROMPT,
            "prefer_character_prompt": True,
            "prefer_character_jailbreak": True,
            "sysprompt": {
                "enabled": False,
                "content": "",
                "post_history": ""
            },
            "instruct": {
                "enabled": False,
                "user_alignment_message": ""
            },
            "context": {
                "story_string": "{{#if system}}{{system}}\n{{/if}}{{#if wiBefore}}{{wiBefore}}\n{{/if}}{{#if description}}{{description}}\n{{/if}}{{#if personality}}{{personality}}\n{{/if}}{{#if scenario}}{{scenario}}\n{{/if}}{{#if wiAfter}}{{wiAfter}}\n{{/if}}{{#if persona}}{{persona}}\n{{/if}}"
            }
        }
        self.chat_metadata = {}
        self.extension_prompts = {}
        
    def get_character_card_fields(self, character_id: Optional[int] = None) -> CharacterCardFields:
        """
        获取角色卡片字段
        
        Args:
            character_id: 角色ID，如果为None则使用当前角色
            
        Returns:
            CharacterCardFields: 角色卡片字段对象
        """
        current_id = character_id if character_id is not None else self.current_character_id
        
        result = CharacterCardFields()
        
        # 获取用户人设
        result.persona = self._base_chat_replace(
            self.power_user_settings.get("persona_description", "").strip(),
            self.name1, self.name2
        )
        
        # 获取角色信息
        if current_id is not None and current_id < len(self.characters):
            character = self.characters[current_id]
            
            # 获取场景文本
            scenario_text = (
                self.chat_metadata.get('scenario', '') or 
                character.get('scenario', '') or 
                ''
            )
            
            # 填充字段
            result.description = self._base_chat_replace(
                character.get('description', '').strip(), 
                self.name1, self.name2
            )
            result.personality = self._base_chat_replace(
                character.get('personality', '').strip(), 
                self.name1, self.name2
            )
            result.scenario = self._base_chat_replace(
                scenario_text.strip(), 
                self.name1, self.name2
            )
            result.mes_examples = self._base_chat_replace(
                character.get('mes_example', '').strip(), 
                self.name1, self.name2
            )
            
            # 系统提示词
            if self.power_user_settings.get("prefer_character_prompt"):
                result.system = self._base_chat_replace(
                    character.get('data', {}).get('system_prompt', '').strip(),
                    self.name1, self.name2
                )
            
            # 越狱指令
            if self.power_user_settings.get("prefer_character_jailbreak"):
                result.jailbreak = self._base_chat_replace(
                    character.get('data', {}).get('post_history_instructions', '').strip(),
                    self.name1, self.name2
                )
            
            # 其他字段
            result.version = character.get('data', {}).get('character_version', '')
            result.char_depth_prompt = self._base_chat_replace(
                character.get('data', {}).get('extensions', {}).get('depth_prompt', {}).get('prompt', '').strip(),
                self.name1, self.name2
            )
            result.creator_notes = self._base_chat_replace(
                character.get('data', {}).get('creator_notes', '').strip(),
                self.name1, self.name2
            )
            
            # 处理群组角色卡片
            if self.selected_group:
                group_cards = self._get_group_character_cards(self.selected_group, current_id)
                if group_cards:
                    result.description = group_cards.description
                    result.personality = group_cards.personality
                    result.scenario = group_cards.scenario
                    result.mes_examples = group_cards.mes_examples
        
        return result
    
    def _base_chat_replace(self, text: str, name1: str, name2: str) -> str:
        """
        基础聊天文本替换
        
        Args:
            text: 原始文本
            name1: 用户名
            name2: 角色名
            
        Returns:
            str: 替换后的文本
        """
        if not text:
            return ""
        
        # 替换用户和角色名称
        text = text.replace("{{user}}", name1)
        text = text.replace("{{char}}", name2)
        text = text.replace("{{name1}}", name1)
        text = text.replace("{{name2}}", name2)
        
        return text
    
    def _get_group_character_cards(self, group_id: str, character_id: int) -> Optional[CharacterCardFields]:
        """
        获取群组角色卡片（简化实现）
        
        Args:
            group_id: 群组ID
            character_id: 角色ID
            
        Returns:
            Optional[CharacterCardFields]: 群组角色卡片字段
        """
        # 这里应该实现群组角色卡片的逻辑
        # 简化实现，返回None
        return None
    
    def substitute_params(self, content: str, name1: Optional[str] = None, 
                         name2: Optional[str] = None, original: Optional[str] = None,
                         group: Optional[str] = None, replace_character_card: bool = True,
                         additional_macro: Optional[Dict] = None) -> str:
        """
        参数替换函数
        
        Args:
            content: 要替换的内容
            name1: 用户名
            name2: 角色名
            original: 原始内容
            group: 群组
            replace_character_card: 是否替换角色卡片
            additional_macro: 额外的宏参数
            
        Returns:
            str: 替换后的内容
        """
        if not content:
            return ""
        
        name1 = name1 or self.name1
        name2 = name2 or self.name2
        
        # 基础替换
        content = self._base_chat_replace(content, name1, name2)
        
        # 替换角色卡片字段
        if replace_character_card:
            fields = self.get_character_card_fields()
            
            # 创建环境变量字典
            environment = {
                'charPrompt': fields.system or '',
                'charInstruction': fields.jailbreak or '',
                'charJailbreak': fields.jailbreak or '',
                'description': fields.description or '',
                'personality': fields.personality or '',
                'scenario': fields.scenario or '',
                'persona': fields.persona or '',
                'mesExamples': lambda: self._format_mes_examples(fields.mes_examples),
                'mesExamplesRaw': fields.mes_examples or '',
                'charVersion': fields.version or '',
                'char_version': fields.version or '',
                'charDepthPrompt': fields.char_depth_prompt or '',
                'creatorNotes': fields.creator_notes or '',
            }
            
            # 替换环境变量
            for key, value in environment.items():
                if callable(value):
                    content = content.replace(f"{{{{{key}}}}}", value())
                else:
                    content = content.replace(f"{{{{{key}}}}}", str(value))
        
        # 替换群组名称
        if group:
            group_value = self._get_group_value(group, name1, name2)
            content = content.replace("{{group}}", group_value)
        
        # 替换额外宏参数
        if additional_macro:
            for key, value in additional_macro.items():
                content = content.replace(f"{{{{{key}}}}}", str(value))
        
        return content
    
    def _get_group_value(self, group: str, name1: str, name2: str) -> str:
        """
        获取群组值
        
        Args:
            group: 群组信息
            name1: 用户名
            name2: 角色名
            
        Returns:
            str: 群组值
        """
        if isinstance(group, str):
            return group
        
        if self.selected_group:
            # 这里应该实现群组成员获取逻辑
            # 简化实现，返回角色名
            return name2
        else:
            return name2
    
    def _format_mes_examples(self, mes_examples: str) -> str:
        """
        格式化对话示例
        
        Args:
            mes_examples: 原始对话示例
            
        Returns:
            str: 格式化后的对话示例
        """
        if not mes_examples:
            return ""
        
        # 解析对话示例
        examples = self._parse_mes_examples(mes_examples)
        
        # 如果是指导模式，格式化示例
        if self.power_user_settings.get("instruct", {}).get("enabled"):
            examples = self._format_instruct_mode_examples(examples, self.name1, self.name2)
        
        return "".join(examples)
    
    def _parse_mes_examples(self, mes_examples: str) -> List[str]:
        """
        解析对话示例
        
        Args:
            mes_examples: 原始对话示例字符串
            
        Returns:
            List[str]: 解析后的对话示例列表
        """
        if not mes_examples:
            return []
        
        # 简单的解析逻辑，按行分割
        lines = mes_examples.strip().split('\n')
        examples = []
        current_example = []
        
        for line in lines:
            line = line.strip()
            if line:
                current_example.append(line)
            elif current_example:
                examples.append('\n'.join(current_example))
                current_example = []
        
        if current_example:
            examples.append('\n'.join(current_example))
        
        return examples
    
    def _format_instruct_mode_examples(self, examples: List[str], name1: str, name2: str) -> List[str]:
        """
        格式化指导模式示例
        
        Args:
            examples: 原始示例列表
            name1: 用户名
            name2: 角色名
            
        Returns:
            List[str]: 格式化后的示例列表
        """
        formatted_examples = []
        
        for example in examples:
            # 替换用户和角色名称
            formatted_example = example.replace("{{user}}", name1)
            formatted_example = formatted_example.replace("{{char}}", name2)
            formatted_examples.append(formatted_example)
        
        return formatted_examples
    
    def render_story_string(self, params: StoryStringParams, 
                           custom_story_string: Optional[str] = None,
                           custom_instruct_settings: Optional[Dict] = None) -> str:
        """
        渲染故事字符串
        
        Args:
            params: 故事字符串参数
            custom_story_string: 自定义故事字符串模板
            custom_instruct_settings: 自定义指导设置
            
        Returns:
            str: 渲染后的故事字符串
        """
        try:
            story_string = custom_story_string or self.power_user_settings["context"]["story_string"]
            instruct_settings = custom_instruct_settings or self.power_user_settings.get("instruct", {})
            
            # 验证故事字符串
            self._validate_story_string(story_string, params)
            
            # 编译模板
            compiled_template = self._compile_template(story_string)
            
            # 渲染模板
            output = compiled_template(params)
            
            # 替换参数
            output = self.substitute_params(output, params.user, params.char)
            
            # 移除开头的换行符
            output = re.sub(r'^\n+', '', output)
            
            # 在末尾添加换行符
            if output and not output.endswith('\n'):
                if not instruct_settings.get("enabled") or instruct_settings.get("wrap"):
                    output += '\n'
            
            return output
            
        except Exception as e:
            logger.error(f"渲染故事字符串时出错: {e}")
            raise
    
    def _compile_template(self, template: str):
        """
        编译模板（简化实现，使用字符串替换）
        
        Args:
            template: 模板字符串
            
        Returns:
            callable: 编译后的模板函数
        """
        def render_template(params):
            result = template
            
            # 处理条件块
            result = self._process_conditional_blocks(result, params)
            
            # 替换变量
            for key, value in params.__dict__.items():
                placeholder = f"{{{{{key}}}}}"
                if placeholder in result:
                    result = result.replace(placeholder, str(value) if value else "")
            
            return result
        
        return render_template
    
    def _process_conditional_blocks(self, template: str, params: StoryStringParams) -> str:
        """
        处理条件块
        
        Args:
            template: 模板字符串
            params: 参数对象
            
        Returns:
            str: 处理后的模板
        """
        # 简化的条件块处理
        # 处理 {{#if field}}...{{/if}} 格式
        
        def replace_conditional(match):
            field_name = match.group(1)
            content = match.group(2)
            
            # 获取字段值
            field_value = getattr(params, field_name, "")
            
            if field_value and str(field_value).strip():
                return content
            else:
                return ""
        
        # 使用正则表达式替换条件块
        pattern = r'\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}'
        result = re.sub(pattern, replace_conditional, template, flags=re.DOTALL)
        
        return result
    
    def _validate_story_string(self, story_string: str, params: StoryStringParams):
        """
        验证故事字符串
        
        Args:
            story_string: 故事字符串
            params: 参数对象
        """
        # 检查是否包含必要的字段
        fields_to_check = ['description', 'personality', 'persona', 'scenario', 'wi_before', 'wi_after']
        
        for field in fields_to_check:
            placeholder = f"{{{{{field}}}}}"
            if placeholder not in story_string:
                field_value = getattr(params, field, "")
                if field_value:
                    logger.warning(f"故事字符串不包含字段 {{{{{field}}}}}, 但该字段有内容: {field_value}")
    
    def set_extension_prompt(self, key: str, value: str, position: int, depth: int = 0,
                           scan: bool = False, role: ExtensionPromptRoles = ExtensionPromptRoles.SYSTEM,
                           filter_func: Optional[callable] = None):
        """
        设置扩展提示词
        
        Args:
            key: 提示词键
            value: 提示词值
            position: 插入位置
            depth: 插入深度
            scan: 是否包含在世界信息扫描中
            role: 提示词角色
            filter_func: 过滤函数
        """
        self.extension_prompts[key] = {
            'value': str(value),
            'position': int(position),
            'depth': int(depth),
            'scan': bool(scan),
            'role': role.value,
            'filter': filter_func,
        }
    
    def get_extension_prompt(self, prompt_type: ExtensionPromptTypes, depth: int = 0,
                           separator: str = '\n', role: ExtensionPromptRoles = ExtensionPromptRoles.SYSTEM,
                           wrap: bool = False) -> str:
        """
        获取扩展提示词
        
        Args:
            prompt_type: 提示词类型
            depth: 深度
            separator: 分隔符
            role: 角色
            wrap: 是否包装
            
        Returns:
            str: 扩展提示词
        """
        # 查找匹配的扩展提示词
        for key, prompt in self.extension_prompts.items():
            if (prompt.get('position') == prompt_type.value and 
                prompt.get('depth') == depth and 
                prompt.get('role') == role.value):
                
                value = prompt.get('value', '')
                
                # 应用过滤函数
                if prompt.get('filter') and callable(prompt['filter']):
                    if not prompt['filter']():
                        continue
                
                return value
        
        return ""
    
    def get_extension_prompt_max_depth(self) -> int:
        """
        获取扩展提示词最大深度
        
        Returns:
            int: 最大深度
        """
        max_depth = 0
        for prompt in self.extension_prompts.values():
            depth = prompt.get('depth', 0)
            max_depth = max(max_depth, depth)
        return max_depth


# 使用示例
if __name__ == "__main__":
    # 创建角色系统实例
    character_system = CharacterSystem()
    
    # 添加示例角色
    character_system.characters.append({
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
    
    character_system.current_character_id = 0
    character_system.name1 = "User"
    character_system.name2 = "Alice"
    
    # 获取角色卡片字段
    fields = character_system.get_character_card_fields()
    print("角色卡片字段:")
    print(f"描述: {fields.description}")
    print(f"性格: {fields.personality}")
    print(f"场景: {fields.scenario}")
    
    # 创建故事字符串参数
    story_params = StoryStringParams(
        description=fields.description,
        personality=fields.personality,
        scenario=fields.scenario,
        char=character_system.name2,
        user=character_system.name1
    )
    
    # 渲染故事字符串
    story_string = character_system.render_story_string(story_params)
    print("\n渲染的故事字符串:")
    print(story_string)
    
    # 测试参数替换
    test_content = "Hello {{user}}, I am {{char}}. {{description}}"
    replaced_content = character_system.substitute_params(test_content)
    print("\n参数替换结果:")
    print(replaced_content) 