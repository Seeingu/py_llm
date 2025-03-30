# py_llm

一个基于 LiteLLM 的命令行工具，支持多种大语言模型的交互式对话。

## 特性

- 支持多种大语言模型（如 deepseek-chat、doubao-1-5-pro 等）
- 交互式对话模式
- 支持从剪贴板读取内容
- 支持多轮对话历史记录
- 支持流式输出

## 安装

本项目使用 Poetry 进行依赖管理。请确保你已安装 Poetry，然后执行：

```bash
# 克隆项目
git clone https://github.com/your-username/py_llm.git
cd py_llm

# 安装依赖
poetry install
```

## 使用方法

### 交互式模式

直接运行命令进入交互式对话模式：

```bash
poetry run python -m py_llm
```

### 单次输入模式

```bash
# 直接输入文本
poetry run python -m py_llm "你的问题"

# 从剪贴板读取内容
poetry run python -m py_llm -p
```

### 对话控制

在交互式模式中：
- 输入 `exit` 或 `quit` 退出程序
- 输入 `clear` 清除对话历史

## 环境变量配置

使用前需要设置以下环境变量：

```bash
# 如果使用 doubao 模型
export DOUBAO_API_KEY="your_api_key"
```

## 依赖项

- Python 3.8+
- litellm
- pyperclip
- requests
- asyncio

## 许可证

MIT