# AI代码助手 - 如何开发大模型应用的演示项目

🤖 **从任务决策、计划生成到ReAct Agent协作的完整AI应用流程实现**

这是一个用于学习和理解大模型应用开发完整流程的演示项目，展示了如何构建一个智能的AI代码助手，涵盖任务路由、智能规划、ReAct Agent执行等核心应用模式。

## 🏳️‍🌈 开源目的

通过这个项目，让读者可以理解本项目的设计模式、架构原理和实现细节，为构建自己的大模型应用提供思路、方案参考。

## 🎯 项目特色

### 核心AI应用模式
- **🧠 智能任务路由**: 自动识别用户意图，分类为开发任务、问答咨询、Bug修复等
- **📋 智能计划生成**: 将复杂任务自动拆解为2-6个可执行步骤
- **🔧 ReAct Agent执行**: 使用LangChain ReAct模式，具备思考-行动-观察能力
- **🛠️ 工具链集成**: 集成文件操作、Git管理、项目启动等工具

### 学习价值
- **完整AI应用架构**: 从输入处理到输出执行的完整流程
- **多模式任务处理**: 简单开发、复杂开发、错误修复、智能问答
- **项目检测与启动**: 支持React、Node.js、Python、Java等多种项目类型
- **实用工具集成**: 文件操作、Git管理、错误诊断等实用功能

## 🏗️ 项目架构

```
ai-code-assistant/
├── config/                     # 配置文件目录
│   └── .env.template          # 环境变量配置模板
├── src/                       # 源代码目录
│   ├── core/                  # 核心业务层
│   │   ├── __init__.py       
│   │   ├── app_context.py     # 应用上下文管理
│   │   ├── router.py          # 任务路由器 - 智能分析用户输入
│   │   ├── planner.py         # 项目计划器 - 任务拆解与规划
│   │   ├── executor.py        # 代码执行器 - ReAct Agent执行
│   │   ├── question_handler.py # 问题解答器 - 技术咨询处理
│   │   ├── project_detector.py # 项目检测器 - 多语言项目支持
│   │   ├── error_fixer.py     # 错误修复器 - 智能诊断和修复
│   │   └── error_rule_engine.py # 错误规则引擎 - 规则匹配系统
│   ├── models/                # 数据模型层
│   │   ├── __init__.py       
│   │   ├── llm_provider.py    # LLM模型提供者
│   │   └── task_types.py      # 任务类型定义
│   ├── tools/                 # 工具层
│   │   ├── __init__.py       
│   │   ├── file_operations.py # 文件操作工具
│   │   ├── git_operations.py  # Git操作工具
│   │   └── shell_operations.py # Shell命令执行工具
│   ├── utils/                 # 通用工具层
│   │   ├── __init__.py       
│   │   ├── config_loader.py   # 配置加载器
│   │   ├── path_utils.py      # 路径处理工具
│   │   ├── ui_helpers.py      # UI辅助工具
│   │   ├── project_helpers.py # 项目管理辅助
│   │   ├── validators.py      # 数据验证器
│   │   └── logger.py          # 日志管理器
│   ├── interfaces/            # 接口层
│   │   ├── __init__.py       
│   │   └── cli.py            # 命令行接口
│   └── __init__.py           
├── .gitignore                # Git忽略文件配置
├── LICENSE                   # 开源许可证
├── README.md                 # 项目说明文档
├── main.py                   # 应用主入口文件
└── requirements.txt          # Python依赖包列表
```

## 🚀 快速开始

### 环境要求
- Python 3.10+
- pip 包管理器

### 1. 克隆项目
```bash
git clone https://github.com/wafu7969/ai-code-assistant
cd ai-code-assistant
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境
复制环境变量模板并配置API密钥：
```bash
cp config/.env.template ./.env
```

编辑 `.env` 文件，填入你的API配置：
```env
# OpenRouter API配置 (推荐)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=anthropic/claude-3-5-sonnet

# 或者使用 OpenAI API
# OPENAI_API_KEY=your_openai_api_key_here
# OPENAI_MODEL=gpt-4

# 项目配置
PROJECT_ROOT=.
OUTPUT_DIR=output  # 生成项目的输出目录

# 开发配置
DEBUG=false
LOG_LEVEL=INFO
```

### 4. 启动应用
## 💡 核心功能演示

### 1. 智能任务路由
AI助手能自动识别用户输入的意图类型：

```python
# 示例：用户输入 "帮我创建一个React购物车组件"
# 路由器分析 → 简单开发任务
# 触发：项目分析 → ReAct执行
```

### 2. 智能计划生成
复杂任务自动拆解为可执行步骤：

```
🧠 任务: "创建一个带购物车功能的React电商网站"
📋 生成计划:
  1. 创建React项目结构和基础配置
  2. 设计商品展示组件和样式
  3. 实现购物车状态管理
  4. 创建用户界面和交互逻辑
  5. 集成支付流程和订单管理
  6. 添加响应式设计和测试
```

### 3. ReAct Agent执行
使用思考-行动-观察模式执行任务：

```
🤖 Thought: 我需要分析用户需求，创建React购物车组件
🔧 Action: get_project_tree
📋 Observation: 发现现有项目结构...
🤖 Thought: 基于现有结构，我需要创建购物车组件
🔧 Action: write_file
📋 Observation: 文件创建成功...
```

### 4. 多项目类型支持
自动检测并支持多种项目类型：

- **Node.js/React**: `npm install && npm run dev`
- **Python/Django**: `pip install -r requirements.txt && python manage.py runserver`
- **Java/Spring**: `mvn spring-boot:run`
- **Go**: `go run main.go`
- **Rust**: `cargo run`

## 🔧 使用示例

### 创建一个系统
```
用户: 帮我创建一个React的OA系统的前端页面
助手: 🤖 正在分析任务类型...
     📋 识别为复杂开发任务，开始制定计划...
     🚀 开始执行开发计划...
     ✅ React的OA系统前端页面创建完成！
```

### 项目错误修复
```
用户: 我的npm run dev报错了，帮我看看
助手: 🔍 正在分析错误信息...
     🛠️ 检测到依赖版本冲突问题
     ⚙️ 正在修复...
     ✅ 错误已修复，项目可以正常启动
```

### 技术咨询问答
```
用户: React Hooks的最佳实践是什么？
助手: 🤖 正在使用ReAct Agent分析并回答问题...
     📚 [详细的技术解答和代码示例]
```

## 🔍 核心组件解析

### 1. TaskRouter - 任务路由器
- **位置**: `src/core/router.py`
- **功能**: 分析用户输入，智能识别任务类型
- **学习点**: 自然语言处理、意图识别、分类算法

### 2. ProjectPlanner - 项目计划器  
- **位置**: `src/core/planner.py`
- **功能**: 复杂任务拆解和步骤规划
- **学习点**: 任务分解、依赖分析、计划生成

### 3. CodeExecutor - 代码执行器
- **位置**: `src/core/executor.py`  
- **功能**: ReAct Agent模式执行，工具链调用
- **学习点**: Agent架构、工具集成、错误处理

### 4. QuestionHandler - 问题解答器
- **位置**: `src/core/question_handler.py`
- **功能**: 智能问答和技术咨询
- **学习点**: 知识检索、上下文理解、回答生成

## AI应用模式

1. **ReAct模式**: Thought → Action → Observation 循环
2. **工具链集成**: LangChain工具生态系统
3. **多模态处理**: 文本分析、代码生成、文件操作
4. **上下文管理**: 项目状态、历史记录、配置管理

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📚️ 学习交流

**欢迎关注我的公众号，获取更多关于大模型应用的学习资源和技术分享。**

![微信公众号二维码](images/wechat.jpg)