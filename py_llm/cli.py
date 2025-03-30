import argparse
import sys
import requests
from litellm import completion, acompletion
import litellm
import asyncio
import os
import traceback
import pyperclip

MODEL = "deepseek/deepseek-chat"
SYSTEM_MESSAGE = "You are an experienced frontend programmer. 回答尽可能使用中文"

async def base_completion_call(input: str, completion_func, model_config: dict, message_history=None):
    # 如果没有提供消息历史，则初始化一个新的历史
    if message_history is None:
        message_history = [
            {"role": "system", "content": SYSTEM_MESSAGE}
        ]
    
    # 添加用户的新输入到消息历史
    message_history.append({"role": "user", "content": input})
    
    try:
        response = await completion_func(**model_config)
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

async def ds_completion_call(input: str, message_history=None):
    model_config = {
        "model": MODEL,
        "messages": message_history or [{"role": "system", "content": SYSTEM_MESSAGE}],
        "stream": True
    }
    return await base_completion_call(input, acompletion, model_config, message_history)

DOUBAO_API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
DOUBAO_MODEL = "openai/doubao-1-5-pro-256k-250115"
async def doubao_completion_call(input: str, message_history=None):
    model_config = {
        "model": DOUBAO_MODEL,
        "api_key": os.environ['DOUBAO_API_KEY'],
        "api_base": DOUBAO_API_BASE,
        "messages": message_history or [{"role": "system", "content": SYSTEM_MESSAGE}],
        "stream": True
    }
    return await base_completion_call(input, acompletion, model_config, message_history)


async def handle_interactive_loop(message_history, completion_callback):
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
            message_history = await completion_callback(user_input, message_history)
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
    await handle_interactive_loop(message_history, doubao_completion_call)

async def single_input_mode(input_text: str, system_message=SYSTEM_MESSAGE):
    """处理单次输入模式的异步函数，支持多轮对话"""
    message_history = [
        {"role": "system", "content": system_message}
    ]
    
    # 处理初始输入
    print()
    message_history = await doubao_completion_call(input_text, message_history)
    print("\n")
    
    # 继续进行多轮对话
    await handle_interactive_loop(message_history, doubao_completion_call)

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

    args = parser.parse_args()
    if args.url is not None:
        raise "not implemented"
    elif args.paste:
        clipboard_content = pyperclip.paste()
        if clipboard_content:
            # 检查是否为链接（简单判断是否以 http:// 或 https:// 开头）
            if clipboard_content.startswith(('http://', 'https://')):
                clipboard_content = f"summarize {clipboard_content}"
            asyncio.run(single_input_mode(clipboard_content))
        else:
            print("剪贴板为空")
    elif args.text:
        asyncio.run(single_input_mode(args.text))
    else:
        # 默认使用交互模式
        asyncio.run(interactive_mode())

