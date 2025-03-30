import argparse
import sys
import requests
from litellm import completion, acompletion
import litellm
import asyncio
import os
import traceback
import pyperclip

DS_MODEL = "deepseek/deepseek-chat"
DS_REASONER_MODEL = "deepseek/deepseek-reasoner"
SYSTEM_MESSAGE = "You are an experienced frontend programmer. 回答尽可能使用中文"

# 模型配置
DS_MODEL_CONFIG = {
    "model": DS_MODEL,
    "messages": None,  # 将在调用时设置
    "stream": True
}
DS_REASONER_MODEL_CONFIG = {
    "model": DS_REASONER_MODEL,
    "messages": None,  # 将在调用时设置
    "stream": True
}

DOUBAO_API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
DOUBAO_MODEL = "openai/doubao-1-5-pro-256k-250115"
DOUBAO_MODEL_CONFIG = {
    "model": DOUBAO_MODEL,
    "api_key": os.environ['DOUBAO_API_KEY'],
    "api_base": DOUBAO_API_BASE,
    "messages": None,  # 将在调用时设置
    "stream": True
}

model_config=DOUBAO_MODEL_CONFIG

async def base_completion_call(input: str,  config: dict, message_history=None):
    # 如果没有提供消息历史，则初始化一个新的历史
    if message_history is None:
        message_history = [
            {"role": "system", "content": SYSTEM_MESSAGE}
        ]
    
    # 添加用户的新输入到消息历史
    message_history.append({"role": "user", "content": input})
    
    try:
        response = await acompletion(**config)
        print(f"response: {response}")
        assistant_response = ""
        async for chunk in response:
            content = chunk.choices[0].delta.get("content", "")
            if content is not None:
                assistant_response += content
                print(content, end="", flush=True)
        
        # 将助手的回复添加到消息历史
        if assistant_response:
            message_history.append({"role": "assistant", "content": assistant_response})
        
        # 返回更新后的消息历史
        return message_history
    except Exception as e:
        print(f"\n错误发生: {traceback.format_exc()}")
        return message_history

async def completion_call(input: str, message_history=None):
    """统一的completion调用函数
    
    Args:
        input: 用户输入的文本
        config: 模型配置字典
        message_history: 消息历史记录，默认为None
    """
    config = model_config.copy()
    config["messages"] = message_history or [{"role": "system", "content": SYSTEM_MESSAGE}]
    return await base_completion_call(input, config, message_history)


async def handle_interactive_loop(message_history):
    """处理交互式对话循环的基础函数
    
    Args:
        message_history: 消息历史记录列表
        completion_callback: 处理用户输入的回调函数
    
    Returns:
        更新后的消息历史记录
    """
    print("多轮对话模式已启动，输入 'exit' 或 'quit' 退出，输入 'clear' 清除对话历史")
    
    while True:
        try:
            user_input = input("> ")
            if user_input.lower() in ['exit', 'quit']:
                break
            elif user_input.lower() == 'clear':
                message_history = [
                    {"role": "system", "content": SYSTEM_MESSAGE}
                ]
                print("对话历史已清除")
                continue
            
            # 调用completion_call并更新消息历史
            print()
            message_history = await completion_call(user_input, message_history)
            print("\n")
        except KeyboardInterrupt:
            print("\n退出交互模式")
            break
        except EOFError:
            break
    
    return message_history

async def interactive_mode():
    """处理交互模式的异步函数"""
    message_history = [
        {"role": "system", "content": SYSTEM_MESSAGE}
    ]
    await handle_interactive_loop(message_history)

async def single_input_mode(input_text: str, system_message=SYSTEM_MESSAGE):
    """处理单次输入模式的异步函数，支持多轮对话"""
    message_history = [
        {"role": "system", "content": system_message}
    ]
    
    # 处理初始输入
    print()
    message_history = await completion_callback(input_text, message_history)
    print("\n")
    
    # 继续进行多轮对话
    await handle_interactive_loop(message_history)

def main():
    """命令行工具的主入口点"""
    parser = argparse.ArgumentParser(
        description="从URL获取内容并显示在命令行中"
    )
    parser.add_argument(
        "-u", "--url",
        required=False,
        help="要获取内容的URL"
    )
    parser.add_argument(
        'text',
        nargs='?',
        help='要处理的文本输入'
    )
    parser.add_argument(
        "-p", "--paste",
        action="store_true",
        help='从剪贴板读取最近一条内容'
    )
    parser.add_argument(
        "-m", "--model",
        choices=['ds', 'doubao'],
        default='doubao',
        help='选择使用的模型配置 (ds: DeepSeek, doubao: 豆包)'
    )

    args = parser.parse_args()
    
    # 根据选择的模型确定使用的回调函数
    # 根据选择的模型确定使用的回调函数和模型名称
    if args.model == 'ds':
        model_name = "DeepSeek"
        model_config = DS_MODEL_CONFIG 
    elif args.model == 'ds-r':
        model_name = "DeepSeek Reasoner"
        model_config = DS_REASONER_MODEL_CONFIG
    else:
        model_name = "豆包"
        model_config = DOUBAO_MODEL_CONFIG
    print(f"\n当前使用的模型: {model_name}\n")

    if args.url is not None:
        raise "not implemented"
    elif args.paste:
        clipboard_content = pyperclip.paste()
        if clipboard_content:
            if clipboard_content.startswith(('http://', 'https://')):
                clipboard_content = f"summarize {clipboard_content}"
            asyncio.run(single_input_mode(clipboard_content ))
        else:
            print("剪贴板为空")
    elif args.text:
        asyncio.run(single_input_mode(args.text ))
    else:
        # 默认使用交互模式
        asyncio.run(interactive_mode())

