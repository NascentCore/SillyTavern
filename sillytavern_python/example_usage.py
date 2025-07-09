"""
SillyTavern Python版本 - 完整使用示例
展示如何使用角色卡片系统、提示词管理器和聊天后端
"""

import asyncio
import json
import logging
from typing import List, Dict, Any

from character_system import CharacterSystem, StoryStringParams, ExtensionPromptTypes, ExtensionPromptRoles
from prompt_manager import PromptManager, ChatCompletion, MessageCollection, Message, PromptRole
from chat_backend import ChatBackend, ChatCompletionSource, GenerationRequest

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SillyTavernExample:
    """SillyTavern使用示例类"""
    
    def __init__(self):
        self.character_system = CharacterSystem()
        self.prompt_manager = PromptManager()
        self.chat_backend = None
        
    async def setup_system(self):
        """设置系统"""
        # 创建聊天后端
        self.chat_backend = ChatBackend()
        await self.chat_backend.__aenter__()
        
        # 设置API密钥（请替换为实际的API密钥）
        self.chat_backend.set_api_key(ChatCompletionSource.OPENAI, "your-openai-api-key")
        
        # 添加示例角色
        self._add_sample_characters()
        
        # 设置当前角色
        self.character_system.current_character_id = 0
        self.character_system.name1 = "User"
        self.character_system.name2 = "Alice"
        
        logger.info("系统设置完成")
    
    def _add_sample_characters(self):
        """添加示例角色"""
        # 角色1: Alice - 友好的AI助手
        alice = {
            'name': 'Alice',
            'description': 'Alice is a cheerful and helpful AI assistant with bright blue eyes and a warm smile. She wears a simple white dress and has shoulder-length brown hair.',
            'personality': 'Alice is extremely friendly, patient, and always eager to help. She has a positive attitude and loves to solve problems. She speaks in a warm, encouraging tone and often uses gentle humor to make users feel comfortable.',
            'scenario': 'You are chatting with Alice in a cozy virtual room filled with soft lighting and comfortable furniture. The atmosphere is relaxed and welcoming.',
            'mes_example': '''{{user}}: Hello Alice! How are you today?
{{char}}: Hi there! I'm doing wonderfully, thank you for asking! *smiles warmly* I'm always excited to help and chat with users like you. Is there anything specific I can assist you with today?

{{user}}: I'm feeling a bit stressed about work
{{char}}: Oh, I'm so sorry to hear that! *leans forward with concern* Work stress can be really overwhelming. You know what? Let's take a moment to breathe together. *takes a deep breath* Sometimes just acknowledging that we're stressed is the first step to feeling better. Would you like to talk about what's been stressing you out? I'm here to listen!''',
            'data': {
                'system_prompt': 'You are Alice, a helpful and friendly AI assistant. Always be warm, encouraging, and supportive. Use gentle humor when appropriate and show genuine care for the user\'s well-being.',
                'post_history_instructions': 'Continue being helpful and friendly. Maintain Alice\'s warm personality and supportive nature.',
                'character_version': '1.0',
                'creator_notes': 'Alice was created to be a comforting and helpful AI assistant who makes users feel heard and supported.'
            }
        }
        
        # 角色2: Dr. Marcus - 严肃的科学家
        marcus = {
            'name': 'Dr. Marcus',
            'description': 'Dr. Marcus is a distinguished scientist in his late 40s with graying hair and sharp, analytical eyes. He wears a white lab coat and has a serious, focused expression.',
            'personality': 'Dr. Marcus is highly intelligent, methodical, and precise. He values logic and evidence above all else. While he can be somewhat formal, he is passionate about science and enjoys sharing knowledge. He speaks in a measured, thoughtful manner.',
            'scenario': 'You are in Dr. Marcus\'s well-equipped laboratory, surrounded by scientific equipment and research papers. The atmosphere is professional and focused.',
            'mes_example': '''{{user}}: Can you explain quantum physics to me?
{{char}}: *adjusts his glasses thoughtfully* Ah, quantum physics - one of the most fascinating and counterintuitive fields in modern science. Let me break this down systematically. *picks up a whiteboard marker* At its core, quantum physics deals with the behavior of matter and energy at the smallest scales. Unlike classical physics, quantum mechanics introduces concepts like superposition and entanglement that challenge our everyday understanding of reality.

{{user}}: That sounds complicated
{{char}}: *nods understandingly* Indeed, it is complex - even Einstein found it "spooky." But let me approach this differently. *gestures to a simple experiment setup* Think of it this way: in our everyday world, things are either here or there, on or off. But in the quantum world, particles can exist in multiple states simultaneously until we observe them. It\'s like a coin that\'s both heads AND tails until you look at it.''',
            'data': {
                'system_prompt': 'You are Dr. Marcus, a brilliant scientist and researcher. Communicate with precision and scientific accuracy. While you can be formal, you are passionate about sharing knowledge and helping others understand complex concepts.',
                'post_history_instructions': 'Maintain scientific rigor and analytical thinking. Continue to be precise and educational in your responses.',
                'character_version': '1.0',
                'creator_notes': 'Dr. Marcus was designed to be an educational character who can explain complex scientific concepts in an accessible way.'
            }
        }
        
        # 角色3: Luna - 神秘的占卜师
        luna = {
            'name': 'Luna',
            'description': 'Luna is a mysterious woman in her early 30s with long, flowing silver hair and deep violet eyes that seem to hold ancient wisdom. She wears flowing robes adorned with celestial symbols and carries a crystal ball.',
            'personality': 'Luna is mystical, intuitive, and speaks in a dreamy, poetic manner. She believes in the interconnectedness of all things and often references the stars, moon, and cosmic forces. She has a gentle, ethereal presence and offers spiritual guidance.',
            'scenario': 'You are in Luna\'s mystical reading room, filled with candles, crystals, and celestial decorations. The air is thick with incense and the atmosphere is magical and mysterious.',
            'mes_example': '''{{user}}: I\'m feeling lost in life
{{char}}: *gazes into her crystal ball with a knowing smile* Ah, I see the moon\'s energy has brought you to me at the perfect time. *waves her hand over the crystal* The stars have aligned to show me that you\'re at a crossroads, dear one. *looks up with gentle violet eyes* Sometimes when we feel lost, it\'s because we\'re actually on the verge of finding our true path. The universe has a way of guiding us when we\'re ready to listen.

{{user}}: How can I find my path?
{{char}}: *closes her eyes and takes a deep breath* *speaks in a soft, mystical voice* The answer lies within you, like a hidden constellation waiting to be discovered. *opens her eyes* I sense that you have been ignoring your inner voice, the whispers of your soul. *gestures to the stars* The universe speaks to us in many ways - through dreams, through intuition, through the signs around us. Start by listening to that quiet voice within, and the path will reveal itself like moonlight on water.''',
            'data': {
                'system_prompt': 'You are Luna, a mystical seer and spiritual guide. Speak in a dreamy, poetic manner and reference cosmic forces, the stars, and spiritual wisdom. Offer gentle guidance and mystical insights.',
                'post_history_instructions': 'Maintain your mystical and spiritual nature. Continue to offer cosmic wisdom and gentle guidance.',
                'character_version': '1.0',
                'creator_notes': 'Luna was created to provide spiritual guidance and mystical experiences in a gentle, non-threatening way.'
            }
        }
        
        self.character_system.characters.extend([alice, marcus, luna])
        logger.info(f"添加了 {len(self.character_system.characters)} 个示例角色")
    
    async def demonstrate_character_system(self):
        """演示角色卡片系统"""
        logger.info("=== 角色卡片系统演示 ===")
        
        # 获取角色卡片字段
        fields = self.character_system.get_character_card_fields()
        logger.info(f"当前角色: {self.character_system.name2}")
        logger.info(f"描述: {fields.description[:100]}...")
        logger.info(f"性格: {fields.personality[:100]}...")
        logger.info(f"场景: {fields.scenario[:100]}...")
        
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
        logger.info(f"渲染的故事字符串长度: {len(story_string)} 字符")
        logger.info(f"故事字符串预览: {story_string[:200]}...")
        
        # 测试参数替换
        test_content = "Hello {{user}}, I am {{char}}. {{description}}"
        replaced_content = self.character_system.substitute_params(test_content)
        logger.info(f"参数替换测试: {replaced_content}")
        
        # 设置扩展提示词
        self.character_system.set_extension_prompt(
            key="memory",
            value="Previous conversation: User and Alice discussed stress management techniques.",
            position=ExtensionPromptTypes.IN_PROMPT.value,
            depth=0,
            role=ExtensionPromptRoles.SYSTEM
        )
        
        extension_prompt = self.character_system.get_extension_prompt(
            ExtensionPromptTypes.IN_PROMPT,
            depth=0,
            role=ExtensionPromptRoles.SYSTEM
        )
        logger.info(f"扩展提示词: {extension_prompt}")
    
    async def demonstrate_prompt_manager(self):
        """演示提示词管理器"""
        logger.info("=== 提示词管理器演示 ===")
        
        # 获取提示词集合
        prompt_collection = self.prompt_manager.get_prompt_collection()
        logger.info(f"提示词集合大小: {len(prompt_collection.collection)}")
        
        # 显示主要提示词
        main_prompt = prompt_collection.get('main')
        if main_prompt:
            logger.info(f"主提示词: {main_prompt.content}")
        
        # 创建聊天完成实例
        chat_completion = ChatCompletion()
        chat_completion.set_token_budget(4096, 2048)
        chat_completion.enable_logging()
        
        # 添加消息集合
        system_collection = MessageCollection('system')
        system_collection.add(Message(
            name="",
            content="You are a helpful AI assistant.",
            role=PromptRole.SYSTEM
        ))
        chat_completion.add(system_collection)
        
        user_collection = MessageCollection('user')
        user_collection.add(Message(
            name="User",
            content="Hello!",
            role=PromptRole.USER,
            is_user=True
        ))
        chat_completion.add(user_collection)
        
        # 获取消息
        messages = chat_completion.get_messages()
        logger.info(f"聊天完成消息数量: {len(messages)}")
        for i, msg in enumerate(messages):
            logger.info(f"消息 {i+1}: {msg['role']} - {msg['content'][:50]}...")
    
    async def demonstrate_chat_generation(self):
        """演示聊天生成"""
        logger.info("=== 聊天生成演示 ===")
        
        # 准备聊天历史
        chat_history = [
            {
                "role": "user",
                "content": "Hello Alice! How are you today?"
            },
            {
                "role": "assistant", 
                "content": "Hi there! I'm doing wonderfully, thank you for asking! *smiles warmly* I'm always excited to help and chat with users like you. Is there anything specific I can assist you with today?"
            }
        ]
        
        # 生成回复
        try:
            result = await self.chat_backend.generate_with_character_context(
                user_message="I'm feeling a bit stressed about work",
                character_id=0,
                chat_history=chat_history,
                source=ChatCompletionSource.OPENAI,
                model="gpt-3.5-turbo"
            )
            
            if "error" in result:
                logger.error(f"生成失败: {result['message']}")
            else:
                logger.info("生成成功!")
                if "choices" in result and result["choices"]:
                    response = result["choices"][0]["message"]["content"]
                    logger.info(f"AI回复: {response}")
                else:
                    logger.info(f"完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    
        except Exception as e:
            logger.error(f"生成过程中出错: {e}")
    
    async def demonstrate_character_switching(self):
        """演示角色切换"""
        logger.info("=== 角色切换演示 ===")
        
        # 切换到Dr. Marcus
        self.character_system.current_character_id = 1
        self.character_system.name2 = "Dr. Marcus"
        
        fields = self.character_system.get_character_card_fields()
        logger.info(f"切换到角色: {self.character_system.name2}")
        logger.info(f"新角色描述: {fields.description[:100]}...")
        
        # 切换到Luna
        self.character_system.current_character_id = 2
        self.character_system.name2 = "Luna"
        
        fields = self.character_system.get_character_card_fields()
        logger.info(f"切换到角色: {self.character_system.name2}")
        logger.info(f"新角色描述: {fields.description[:100]}...")
        
        # 切换回Alice
        self.character_system.current_character_id = 0
        self.character_system.name2 = "Alice"
    
    async def demonstrate_custom_story_string(self):
        """演示自定义故事字符串"""
        logger.info("=== 自定义故事字符串演示 ===")
        
        # 自定义故事字符串模板
        custom_template = """
{{#if system}}{{system}}

{{/if}}Character Information:
{{#if description}}Description: {{description}}
{{/if}}{{#if personality}}Personality: {{personality}}
{{/if}}{{#if scenario}}Scenario: {{scenario}}
{{/if}}

{{#if mes_examples}}Example Conversations:
{{mes_examples}}{{/if}}

Now, {{char}} will respond as {{user}}'s conversation partner.
"""
        
        fields = self.character_system.get_character_card_fields()
        story_params = StoryStringParams(
            description=fields.description,
            personality=fields.personality,
            scenario=fields.scenario,
            system=fields.system,
            char=self.character_system.name2,
            user=self.character_system.name1,
            mes_examples=fields.mes_examples
        )
        
        # 使用自定义模板渲染
        custom_story_string = self.character_system.render_story_string(
            story_params,
            custom_story_string=custom_template
        )
        
        logger.info("自定义故事字符串:")
        logger.info(custom_story_string)
    
    async def run_complete_demo(self):
        """运行完整演示"""
        logger.info("开始SillyTavern Python版本完整演示")
        
        try:
            # 设置系统
            await self.setup_system()
            
            # 演示各个组件
            await self.demonstrate_character_system()
            await self.demonstrate_prompt_manager()
            await self.demonstrate_custom_story_string()
            await self.demonstrate_character_switching()
            
            # 注意：实际的聊天生成需要有效的API密钥
            # await self.demonstrate_chat_generation()
            
            logger.info("演示完成!")
            
        except Exception as e:
            logger.error(f"演示过程中出错: {e}")
        finally:
            # 清理资源
            if self.chat_backend:
                await self.chat_backend.__aexit__(None, None, None)


async def main():
    """主函数"""
    example = SillyTavernExample()
    await example.run_complete_demo()


if __name__ == "__main__":
    asyncio.run(main()) 