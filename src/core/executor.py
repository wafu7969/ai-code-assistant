"""
代码执行器模块

负责执行具体的开发步骤，生成代码文件
"""
import re
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from ..models.llm_provider import LLMProvider
from ..tools.file_operations import build_file_tools
from ..tools.git_operations import build_git_tools
from ..tools.shell_operations import ShellExecutor
from ..core.error_fixer import ErrorFixer
from ..utils.path_utils import PathUtils
from .project_detector import ProjectDetector


class CodeExecutor:
    """代码执行器"""
    
    def __init__(self, root: Optional[str] = None, output_dir: str = "output"):
        """
        初始化代码执行器
        
        Args:
            root: 项目根目录
            output_dir: 输出目录
        """
        self.llm_provider = LLMProvider(root)
        self.path_utils = PathUtils(root)
        self.output_dir = output_dir
        self._tools = None
        self.shell_executor = ShellExecutor(timeout=300)
        self.error_fixer = ErrorFixer()
    
    def get_tools(self) -> List:
        """
        获取工具列表
        
        Returns:
            工具列表
        """
        if self._tools is None:
            # 对于绝对路径的输出目录，将输出目录作为根目录，避免工具操作AI助手的源码目录
            output_path = Path(self.output_dir)
            if output_path.is_absolute():
                # 绝对路径：以输出目录的父目录作为根目录，输出目录名称作为相对目录
                root_dir = str(output_path.parent)
                output_name = output_path.name
            else:
                # 相对路径：保持原有逻辑
                root_dir = str(self.path_utils.base_dir)
                output_name = self.output_dir
                
            file_tools = build_file_tools(root_dir, output_name)
            git_tools = build_git_tools(root_dir, output_name)
            self._tools = file_tools + git_tools
        
        return self._tools
    
    def execute_step(
        self, 
        task_content: str, 
        step: Dict[str, str], 
        history: str = ""
    ) -> str:
        """
        执行单个开发步骤
        
        Args:
            task_content: 任务内容
            step: 步骤信息
            history: 历史执行记录

        Returns:
            执行结果
        """
        model = self.llm_provider.load_model()
        
        if model is None:
            raise RuntimeError("LLM模型未正确加载，无法执行开发步骤")
        
        tools = self.get_tools()
        
        if not tools:
            raise RuntimeError("工具未正确加载，无法执行开发步骤")
        
        # 首先尝试使用ReAct Agent执行
        try:
            return self._execute_with_tools(model, tools, task_content, step, history)
        except Exception as e:
            print(f"⚠️ ReAct Agent执行失败: {e}")
            print("🔄 切换到直接执行方法...")
            return self._execute_with_direct_method(model, tools, task_content, step, history)
    
    def _execute_with_tools(
        self, 
        model: Any, 
        tools: List, 
        task_content: str, 
        step: Dict[str, str], 
        history: str
    ) -> str:
        """
        使用ReAct Agent执行步骤
        
        Args:
            model: LLM模型
            tools: 工具列表
            task_content: 任务内容
            step: 步骤信息
            history: 历史记录
            
        Returns:
            执行结果
        """
        try:
            from langchain.agents import create_react_agent, AgentExecutor
            from langchain_core.prompts import PromptTemplate
            
            print(f"🤖 使用ReAct Agent执行步骤: {step.get('title', '未知步骤')}")
            
            # 分析任务内容
            task_analysis = self._analyze_task_content(task_content)
            print(f"🎯 任务分析: {task_analysis['original_content']}")
            print(f"📋 建议文件类型: {task_analysis['suggested_file_types']}")
            
            # 错误计数器
            format_error_count = 0
            max_format_errors = 3  # 最多允许3次格式错误
            
            # 自定义解析错误处理函数
            def custom_parsing_error_handler(error_message: str) -> str:
                """自定义解析错误处理，避免无限循环"""
                nonlocal format_error_count
                format_error_count += 1
                
                print(f"🚨 第{format_error_count}次解析错误: {error_message}")
                
                if format_error_count >= max_format_errors:
                    print(f"⚠️ 解析错误次数达到上限({max_format_errors})，切换到直接执行模式")
                    raise Exception(f"解析错误次数过多，切换到备用模式")
                
                if "Invalid Format" in error_message and "Missing 'Action:' after 'Thought:'" in error_message:
                    print("⚠️ 检测到ReAct格式错误，尝试修正...")
                    return "请使用正确的格式: Thought: 你的思考过程 Action: 选择一个工具 Action Input: 工具的输入"
                elif "Invalid Format" in error_message:
                    print(f"⚠️ 检测到格式错误，尝试修正...")
                    return "请遵循标准的ReAct格式: Thought -> Action -> Action Input -> Observation"
                
                return f"解析错误: {error_message}"
            
            # 构建ReAct Agent提示 - 使用标准ReAct格式
            react_prompt = PromptTemplate.from_template("""
                Answer the following questions as best you can. You have access to the following tools:

                {tools}

                Use the following format:

                Question: the input question you must answer
                Thought: you should always think about what to do
                Action: the action to take, should be one of [{tool_names}]
                Action Input: the input to the action
                Observation: the result of the action
                ... (this Thought/Action/Action Input/Observation can repeat N times)
                Thought: I now know the final answer
                Final Answer: the final answer to the original input question

                Begin!

                Question: {input}
                Thought: 我需要理解用户的需求，然后分析现有项目结构来完成开发任务。
                {agent_scratchpad}
            """)
            
            # 创建Agent
            agent = create_react_agent(model, tools, react_prompt)
            agent_executor = AgentExecutor(
                agent=agent, 
                tools=tools, 
                verbose=True,
                max_iterations=120,  # 迭代次数
                max_execution_time=3000,  # 50分钟超时
                handle_parsing_errors=custom_parsing_error_handler,
                return_intermediate_steps=True  # 返回中间步骤而不是使用early_stopping_method
            )
            
            # 构建输入 - 将步骤信息合并到任务内容中
            full_task_content = f"""
                任务: {task_content}
                当前步骤: {step.get('title', '步骤')}
                步骤详情: {step.get('detail', '')}

                任务分析:
                - 是否为页面: {task_analysis['is_page']}
                - 是否为组件: {task_analysis['is_component']}
                - 是否需要表单: {task_analysis['requires_form']}
                - 是否需要数据处理: {task_analysis['requires_data']}
                - 是否需要交互功能: {task_analysis['requires_interactive']}
                - 建议文件类型: {task_analysis['suggested_file_types']}
                """
            
            agent_input = {
                "input": full_task_content.strip()
            }
            
            # 执行Agent
            result = agent_executor.invoke(agent_input)
            
            final_answer = result.get('output', '任务完成')
            
            # 检查是否因为迭代限制而停止
            if "iteration limit" in final_answer.lower() or "time limit" in final_answer.lower():
                print(f"⚠️ Agent达到限制: {final_answer}")
                # 抛出异常，触发备用方案
                raise Exception(f"Agent达到执行限制: {final_answer}")
            
            print(f"✅ Agent执行完成: {final_answer}")
            return final_answer
            
        except Exception as e:
            print(f"❌ ReAct Agent执行失败: {str(e)}")
            print("🔄 回退到直接执行模式")
            return self._execute_with_direct_method(model, tools, task_content, step, history)
    
    def _analyze_task_content(self, task_content: str) -> dict:
        """
        分析任务内容，提取关键信息和技术栈
        
        Args:
            task_content: 任务内容
            
        Returns:
            包含任务分析结果的字典
        """
        content_lower = task_content.lower()
        
        # 前端框架检测
        frontend_frameworks = {
            "react": any(keyword in content_lower for keyword in ['react', 'jsx', 'hooks', 'useState', 'useEffect']),
            "vue": any(keyword in content_lower for keyword in ['vue', 'vue3', 'composition api', 'options api', 'vite']),
            "angular": any(keyword in content_lower for keyword in ['angular', 'ng', 'typescript angular', 'angular cli']),
            "svelte": any(keyword in content_lower for keyword in ['svelte', 'sveltekit']),
            "nextjs": any(keyword in content_lower for keyword in ['next.js', 'nextjs', 'next']),
            "nuxt": any(keyword in content_lower for keyword in ['nuxt', 'nuxt.js', 'nuxtjs']),
        }
        
        # 后端框架检测
        backend_frameworks = {
            "express": any(keyword in content_lower for keyword in ['express', 'express.js', 'nodejs api']),
            "fastapi": any(keyword in content_lower for keyword in ['fastapi', 'fast api', 'python api']),
            "django": any(keyword in content_lower for keyword in ['django', 'django rest']),
            "flask": any(keyword in content_lower for keyword in ['flask', 'flask api']),
            "spring": any(keyword in content_lower for keyword in ['spring', 'spring boot', 'springboot']),
            "gin": any(keyword in content_lower for keyword in ['gin', 'golang gin', 'go gin']),
            "rails": any(keyword in content_lower for keyword in ['rails', 'ruby on rails', 'ror']),
        }
        
        # 移动端框架检测
        mobile_frameworks = {
            "react_native": any(keyword in content_lower for keyword in ['react native', 'rn', 'expo']),
            "flutter": any(keyword in content_lower for keyword in ['flutter', 'dart']),
            "ionic": any(keyword in content_lower for keyword in ['ionic', 'cordova']),
            "xamarin": any(keyword in content_lower for keyword in ['xamarin', 'xamarin.forms']),
        }
        
        # 编程语言检测
        languages = {
            "javascript": any(keyword in content_lower for keyword in ['javascript', 'js', 'node', 'npm']),
            "typescript": any(keyword in content_lower for keyword in ['typescript', 'ts', 'tsx']),
            "python": any(keyword in content_lower for keyword in ['python', 'py', 'pip']),
            "java": any(keyword in content_lower for keyword in ['java', 'maven', 'gradle', 'spring boot']),
            "csharp": any(keyword in content_lower for keyword in ['c#', 'csharp', '.net', 'dotnet']),
            "golang": any(keyword in content_lower for keyword in ['go', 'golang', 'go mod']),
            "rust": any(keyword in content_lower for keyword in ['rust', 'cargo']),
            "php": any(keyword in content_lower for keyword in ['php', 'composer']),
            "ruby": any(keyword in content_lower for keyword in ['ruby', 'gem']),
        }
        
        # 数据库和存储检测
        databases = {
            "mysql": any(keyword in content_lower for keyword in ['mysql', 'mariadb']),
            "postgresql": any(keyword in content_lower for keyword in ['postgresql', 'postgres', 'pg']),
            "mongodb": any(keyword in content_lower for keyword in ['mongodb', 'mongo']),
            "redis": any(keyword in content_lower for keyword in ['redis', '缓存']),
            "sqlite": any(keyword in content_lower for keyword in ['sqlite', 'sqlite3']),
        }
        
        # CSS框架和工具检测
        css_frameworks = {
            "tailwind": any(keyword in content_lower for keyword in ['tailwind', 'tailwindcss']),
            "bootstrap": any(keyword in content_lower for keyword in ['bootstrap', 'bs']),
            "antd": any(keyword in content_lower for keyword in ['ant design', 'antd']),
            "mui": any(keyword in content_lower for keyword in ['material-ui', 'mui', 'material ui']),
            "chakra": any(keyword in content_lower for keyword in ['chakra ui', 'chakra']),
            "sass": any(keyword in content_lower for keyword in ['sass', 'scss']),
            "less": any(keyword in content_lower for keyword in ['less']),
        }
        
        # 基本信息提取
        analysis = {
            "original_content": task_content,
            "content_lower": content_lower,
            "is_page": any(keyword in content_lower for keyword in ['页面', 'page', '页', 'html']),
            "is_component": any(keyword in content_lower for keyword in ['组件', 'component', '模块']),
            "is_app": any(keyword in content_lower for keyword in ['应用', 'app', '系统', 'system']),
            "requires_form": any(keyword in content_lower for keyword in ['表单', 'form', '输入', 'input', '提交']),
            "requires_data": any(keyword in content_lower for keyword in ['数据', 'data', '列表', 'list', '表格', 'table']),
            "requires_interactive": any(keyword in content_lower for keyword in ['交互', '点击', 'click', '按钮', 'button']),
            "requires_api": any(keyword in content_lower for keyword in ['api', '接口', 'rest', 'graphql']),
            "requires_auth": any(keyword in content_lower for keyword in ['登录', '注册', '认证', 'auth', 'login', 'register']),
            
            # 技术栈检测结果
            "frontend_frameworks": {k: v for k, v in frontend_frameworks.items() if v},
            "backend_frameworks": {k: v for k, v in backend_frameworks.items() if v},
            "mobile_frameworks": {k: v for k, v in mobile_frameworks.items() if v},
            "languages": {k: v for k, v in languages.items() if v},
            "databases": {k: v for k, v in databases.items() if v},
            "css_frameworks": {k: v for k, v in css_frameworks.items() if v},
        }
        
        # 智能文件类型推断
        file_types = self._infer_file_types(analysis)
        analysis["suggested_file_types"] = file_types
        
        # 生成技术栈摘要
        analysis["tech_stack_summary"] = self._generate_tech_summary(analysis)
        
        return analysis
    
    def _infer_file_types(self, analysis: dict) -> list:
        """
        基于技术栈分析智能推断文件类型
        
        Args:
            analysis: 任务分析结果
            
        Returns:
            推荐的文件扩展名列表
        """
        file_types = []
        
        # 前端框架文件类型
        if analysis["frontend_frameworks"]:
            if "react" in analysis["frontend_frameworks"]:
                if analysis["languages"].get("typescript"):
                    file_types.extend(["tsx", "ts"])
                else:
                    file_types.extend(["jsx", "js"])
            elif "vue" in analysis["frontend_frameworks"]:
                file_types.append("vue")
                if analysis["languages"].get("typescript"):
                    file_types.append("ts")
            elif "angular" in analysis["frontend_frameworks"]:
                file_types.extend(["ts", "html"])
            elif "svelte" in analysis["frontend_frameworks"]:
                file_types.append("svelte")
            
            # Next.js 特殊处理
            if "nextjs" in analysis["frontend_frameworks"]:
                file_types.extend(["tsx", "ts", "js"])
            
            # CSS 框架
            if analysis["css_frameworks"]:
                if "sass" in analysis["css_frameworks"]:
                    file_types.append("scss")
                elif "less" in analysis["css_frameworks"]:
                    file_types.append("less")
                else:
                    file_types.append("css")
            else:
                file_types.append("css")
        
        # 后端框架文件类型
        if analysis["backend_frameworks"]:
            if "express" in analysis["backend_frameworks"]:
                file_types.append("js")
            elif "fastapi" in analysis["backend_frameworks"] or "django" in analysis["backend_frameworks"] or "flask" in analysis["backend_frameworks"]:
                file_types.append("py")
            elif "spring" in analysis["backend_frameworks"]:
                file_types.append("java")
            elif "gin" in analysis["backend_frameworks"]:
                file_types.append("go")
            elif "rails" in analysis["backend_frameworks"]:
                file_types.append("rb")
        
        # 移动端框架文件类型
        if analysis["mobile_frameworks"]:
            if "react_native" in analysis["mobile_frameworks"]:
                if analysis["languages"].get("typescript"):
                    file_types.extend(["tsx", "ts"])
                else:
                    file_types.extend(["jsx", "js"])
            elif "flutter" in analysis["mobile_frameworks"]:
                file_types.append("dart")
            elif "ionic" in analysis["mobile_frameworks"]:
                file_types.extend(["ts", "html", "css"])
        
        # 基于编程语言推断
        if analysis["languages"]:
            if "python" in analysis["languages"] and "py" not in file_types:
                file_types.append("py")
            elif "java" in analysis["languages"] and "java" not in file_types:
                file_types.append("java")
            elif "csharp" in analysis["languages"]:
                file_types.append("cs")
            elif "golang" in analysis["languages"] and "go" not in file_types:
                file_types.append("go")
            elif "rust" in analysis["languages"]:
                file_types.append("rs")
            elif "php" in analysis["languages"]:
                file_types.append("php")
            elif "ruby" in analysis["languages"] and "rb" not in file_types:
                file_types.append("rb")
        
        # 默认Web文件
        if not file_types or analysis["is_page"]:
            if not any(ext in file_types for ext in ["html", "tsx", "jsx", "vue", "svelte"]):
                file_types.append("html")
        
        # 配置和数据文件
        if analysis["requires_api"] or analysis["backend_frameworks"]:
            if "json" not in file_types:
                file_types.append("json")
        
        # 移除重复并排序
        unique_types = list(dict.fromkeys(file_types))
        
        # 按优先级排序
        priority_order = ["tsx", "jsx", "vue", "svelte", "ts", "js", "py", "java", "go", "cs", "rs", "php", "rb", "dart", "html", "css", "scss", "less", "json"]
        sorted_types = sorted(unique_types, key=lambda x: priority_order.index(x) if x in priority_order else 999)
        
        return sorted_types
    
    def _generate_tech_summary(self, analysis: dict) -> str:
        """
        生成技术栈摘要
        
        Args:
            analysis: 任务分析结果
            
        Returns:
            技术栈摘要字符串
        """
        summary_parts = []
        
        # 前端技术栈
        if analysis["frontend_frameworks"]:
            frameworks = list(analysis["frontend_frameworks"].keys())
            summary_parts.append(f"前端: {', '.join(frameworks).upper()}")
        
        # 后端技术栈
        if analysis["backend_frameworks"]:
            frameworks = list(analysis["backend_frameworks"].keys())
            summary_parts.append(f"后端: {', '.join(frameworks).upper()}")
        
        # 移动端技术栈
        if analysis["mobile_frameworks"]:
            frameworks = list(analysis["mobile_frameworks"].keys())
            summary_parts.append(f"移动端: {', '.join(frameworks).upper()}")
        
        # 编程语言
        if analysis["languages"]:
            languages = list(analysis["languages"].keys())
            summary_parts.append(f"语言: {', '.join(languages).upper()}")
        
        # 数据库
        if analysis["databases"]:
            databases = list(analysis["databases"].keys())
            summary_parts.append(f"数据库: {', '.join(databases).upper()}")
        
        # CSS框架
        if analysis["css_frameworks"]:
            css_frameworks = list(analysis["css_frameworks"].keys())
            summary_parts.append(f"样式: {', '.join(css_frameworks).upper()}")
        
        return " | ".join(summary_parts) if summary_parts else "通用Web技术栈"
    
    def _execute_with_direct_method(
        self, 
        model: Any, 
        tools: List, 
        task_content: str, 
        step: Dict[str, str], 
        history: str
    ) -> str:
        """
        直接执行方法（作为Agent失败时的备选方案）
        
        Args:
            model: LLM模型
            tools: 工具列表
            task_content: 任务内容
            step: 步骤信息
            history: 历史记录
            
        Returns:
            执行结果
        """
        from langchain_core.messages import HumanMessage
        import json
        
        print(f"📝 直接执行步骤: {step.get('title', '未知步骤')}")
        
        # 分析任务内容
        task_analysis = self._analyze_task_content(task_content)
        
        # 构建动态prompt
        prompt_text = f"""
你是一个专业的代码生成助手。请根据用户的具体需求生成相应的代码。

用户需求: {task_content}
当前步骤: {step.get('title', '步骤')}
步骤详情: {step.get('detail', '')}

任务分析:
- 是否为页面: {task_analysis['is_page']}
- 是否为组件: {task_analysis['is_component']}
- 是否需要表单: {task_analysis['requires_form']}
- 是否需要数据处理: {task_analysis['requires_data']}
- 是否需要交互功能: {task_analysis['requires_interactive']}
- 建议文件类型: {task_analysis['suggested_file_types']}

请根据用户需求和分析结果生成相应的代码文件:
1. 分析用户的具体需求，确定需要什么功能
2. 根据功能需求决定文件类型和内容
3. 生成完整可用的代码
4. 确保代码清晰规范，可以直接运行

不要被固定模板限制，要根据实际需求灵活生成代码。
"""

        # 调用模型生成代码
        response = model.invoke([HumanMessage(content=prompt_text)])
        code_content = response.content
        
        print(f"📝 生成的代码长度: {len(code_content)}")
        
        # 让LLM自己决定如何创建和写入文件
        # 这样可以根据具体需求灵活生成不同类型的代码
        print(f"📝 生成的代码长度: {len(code_content)}")
        
        # 尝试从生成的内容中提取文件信息
        # 如果LLM没有使用工具，我们提供一个简单的后备方案
        if "write_file" not in code_content and "Action:" not in code_content:
            print("🔄 LLM未使用工具格式，尝试解析并写入文件...")
            return self._parse_and_create_files_from_content(code_content, tools, task_analysis)
        
        return f"代码生成完成，长度: {len(code_content)}"
    
    def _parse_and_create_files_from_content(self, content: str, tools: List, task_analysis: dict) -> str:
        """
        从LLM生成的内容中解析并创建文件
        
        Args:
            content: LLM生成的内容
            tools: 工具列表
            task_analysis: 任务分析结果
            
        Returns:
            执行结果
        """
        import re
        
        # 找到write_file工具
        write_tool = None
        for tool in tools:
            if tool.name == "write_file":
                write_tool = tool
                break
        
        if not write_tool:
            return "错误: 未找到write_file工具"
        
        files_created = []
        
        # 尝试从内容中提取代码块
        # 匹配 ```类型 或 ```文件名 格式的代码块
        code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', content, re.DOTALL)
        
        if not code_blocks:
            # 如果没有找到代码块，尝试其他格式
            # 匹配文件名: 内容格式
            file_patterns = re.findall(r'([a-zA-Z0-9_-]+\.\w+)[:：]\s*\n(.*?)(?=\n[a-zA-Z0-9_-]+\.\w+[:：]|\Z)', content, re.DOTALL)
            if file_patterns:
                for filename, file_content in file_patterns:
                    self._create_file_with_tool(write_tool, filename.strip(), file_content.strip(), files_created)
            else:
                # 最后的后备方案：根据任务分析智能生成基本文件
                return self._create_default_files_based_on_analysis(write_tool, task_analysis, content, files_created)
        else:
            # 处理代码块
            file_extensions = {
                'html': '.html',
                'css': '.css', 
                'javascript': '.js',
                'js': '.js',
                'python': '.py',
                'py': '.py'
            }
            
            for i, (file_type, file_content) in enumerate(code_blocks):
                if file_type.lower() in file_extensions:
                    ext = file_extensions[file_type.lower()]
                    filename = f"generated_{i+1}{ext}"
                    if ext == '.html':
                        filename = "index.html"
                    elif ext == '.css':
                        filename = "style.css"
                    elif ext == '.js':
                        filename = "script.js"
                    
                    self._create_file_with_tool(write_tool, filename, file_content.strip(), files_created)
        
        if files_created:
            result = f"成功解析并创建了 {len(files_created)} 个文件: {', '.join(files_created)}"
        else:
            result = "未能从生成的内容中识别出文件，但内容已生成"
        
        print(f"✅ {result}")
        return result
    
    def _create_file_with_tool(self, write_tool, filename: str, content: str, files_created: list):
        """使用工具创建文件"""
        try:
            file_input = json.dumps({"path": filename, "content": content})
            print(f"📝 准备写入文件: {filename}, 内容长度: {len(content)}")
            result = write_tool.func(file_input)
            if not result.startswith("错误"):
                files_created.append(filename)
                print(f"📁 创建文件: {filename}")
            else:
                print(f"❌ 创建文件失败 {filename}: {result}")
        except Exception as e:
            print(f"❌ 创建文件异常 {filename}: {e}")
    
    def _create_default_files_based_on_analysis(self, write_tool, task_analysis: dict, content: str, files_created: list) -> str:
        """根据任务分析创建默认文件"""
        # 根据分析结果决定创建什么文件
        if task_analysis['is_page'] or 'html' in task_analysis['suggested_file_types']:
            # 创建基本HTML文件，内容为LLM生成的内容
            html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>生成的页面</title>
</head>
<body>
    <!-- LLM生成的内容 -->
    {content}
</body>
</html>"""
            self._create_file_with_tool(write_tool, "index.html", html_content, files_created)
        else:
            # 创建文本文件
            self._create_file_with_tool(write_tool, "generated_code.txt", content, files_created)
        
        return f"基于任务分析创建了默认文件: {', '.join(files_created)}"
    
    def launch_and_test_project(self, project_path: str = None) -> str:
        """
        启动生成的项目并进行错误检测
        
        Args:
            project_path: 项目路径，默认为output目录
            
        Returns:
            启动结果和错误修复信息
        """
        if not project_path:
            project_path = self.output_dir
            
        print(f"🚀 启动项目: {project_path}")
        
        # 检测项目类型并选择启动命令
        launch_command = self._detect_launch_command(project_path)
        
        if not launch_command:
            return "❌ 无法识别项目类型，无法启动"
            
        print(f"⚙️ 执行启动命令: {launch_command}")
        
        # 执行启动命令（对于服务器类型的项目使用非阻塞启动）
        server_commands = [
            "server", "serve", "dev", "start", 
            "http.server", "runserver", "bootRun",
            "cargo run", "go run", "dotnet run"
        ]
        is_server_command = any(cmd in launch_command.lower() for cmd in server_commands)
        
        if is_server_command:
            # 使用非阻塞方式启动服务器
            success, process, message = self.shell_executor.start_server(launch_command, cwd=project_path)
            
            if success:
                print("✅ 项目启动成功!")
                result = f"项目启动成功: {message}"
                
                # 如果是HTTP服务器，尝试访问验证
                if "http.server" in launch_command:
                    import time
                    import requests
                    
                    try:
                        time.sleep(2)  # 等待服务器完全启动
                        response = requests.get("http://localhost:8000", timeout=5)
                        if response.status_code == 200:
                            result += "\n🌐 服务器可正常访问: http://localhost:8000"
                        else:
                            result += f"\n⚠️ 服务器响应异常，状态码: {response.status_code}"
                    except Exception as e:
                        result += f"\n⚠️ 无法验证服务器访问: {e}"
                        
                        # 检查是否是由于依赖缺失导致的错误
                        error_msg = str(e)
                        if "requests" in error_msg or "ModuleNotFoundError" in error_msg:
                            print("🔍 检测到依赖缺失，正在生成修复建议...")
                            errors = self.error_fixer.detect_errors(error_msg)
                            if errors:
                                suggestions = self.error_fixer.suggest_fixes(errors)
                                print(f"💡 修复建议: {suggestions}")
                                result += f"\n🔧 修复建议: {suggestions}"
                    
                    # 停止服务器进程
                    try:
                        process.terminate()
                        process.wait(timeout=3)
                        result += "\n🔄 测试完成，服务器已停止"
                    except:
                        process.kill()
                        result += "\n🔄 测试完成，服务器已强制停止"
                        
                return result
            else:
                print(f"❌ 启动失败: {message}")
                
                # 检测错误并提供修复建议
                errors = self.error_fixer.detect_errors(message)
                if errors:
                    print("🔍 检测到错误，正在生成修复建议...")
                    suggestions = self.error_fixer.suggest_fixes(errors)
                    print(f"💡 修复建议: {suggestions}")
                    
                    # 尝试应用修复
                    fix_result = self.error_fixer.apply_fixes(suggestions)
                    print(f"🔧 修复应用结果: {fix_result}")
                    
                    return f"启动失败，已提供修复建议。错误: {message}\n修复建议: {suggestions}"
                else:
                    return f"启动失败: {message}"
        else:
            # 使用阻塞方式执行普通命令
            return_code, stdout, stderr = self.shell_executor.execute(launch_command, cwd=project_path)
            
            if return_code != 0:
                print(f"❌ 启动失败: {stderr}")
                
                # 检测错误并提供修复建议
                errors = self.error_fixer.detect_errors(stderr)
                if errors:
                    suggestions = self.error_fixer.suggest_fixes(errors)
                    self.error_fixer.apply_fixes(suggestions)
                    return f"启动失败，已提供修复建议。错误: {stderr}"
                else:
                    return f"启动失败: {stderr}"
            
            print("✅ 项目启动成功!")
        return f"项目启动成功: {stdout}"
    
    def _detect_launch_command(self, project_path: str) -> str:
        """
        智能检测项目类型并返回合适的启动命令
        
        Args:
            project_path: 项目路径
            
        Returns:
            启动命令
        """        
        detector = ProjectDetector()
        result = detector.detect_and_generate(Path(project_path))
        return result.get("launch_command", "")
    
    def _combine_commands(self, *commands) -> str:
        """
        跨平台命令组合，兼容 PowerShell 和 Bash
        
        Args:
            *commands: 要组合的命令列表
            
        Returns:
            组合后的命令字符串
        """
        # 过滤空命令
        valid_commands = [cmd.strip() for cmd in commands if cmd and cmd.strip()]
        
        if not valid_commands:
            return ""
        
        if len(valid_commands) == 1:
            return valid_commands[0]
        
        # PowerShell 和 Bash 都支持 && 运算符来连接命令
        # && 确保前一个命令成功执行后才执行下一个命令
        return " && ".join(valid_commands)
    
    def _detect_nodejs_launch_command(self, path: Path) -> str:
        """检测Node.js项目启动命令"""
        try:
            # 读取package.json
            package_json_path = path / "package.json"
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            scripts = package_data.get('scripts', {})
            
            # 更严格的依赖检查：检查node_modules是否存在且package-lock.json是否匹配
            node_modules_exists = (path / "node_modules").exists()
            package_lock_exists = (path / "package-lock.json").exists()
            
            # 即使node_modules存在，也要检查是否需要更新依赖
            # 如果没有package-lock.json，说明可能是首次安装
            need_install = not node_modules_exists or not package_lock_exists
            
            # 准备安装命令和启动命令
            install_cmd = "npm install" if need_install else ""
            
            # 按优先级检查启动脚本
            start_scripts = ['dev', 'start', 'serve', 'run']
            for script in start_scripts:
                if script in scripts:
                    start_cmd = f"npm run {script}"
                    return self._combine_commands(install_cmd, start_cmd)
            
            # 检查主入口文件
            main_file = package_data.get('main', 'index.js')
            if (path / main_file).exists():
                start_cmd = f"node {main_file}"
                return self._combine_commands(install_cmd, start_cmd)
                
            # 默认尝试npm start
            start_cmd = "npm start"
            return self._combine_commands(install_cmd, start_cmd)
            
        except Exception as e:
            print(f"解析package.json失败: {e}")
            return self._combine_commands("npm install", "npm start")
    
    def _detect_python_launch_command(self, path: Path) -> str:
        """检测Python项目启动命令"""
        # 智能检测入口文件的优先级
        entry_candidates = [
            'main.py', 'app.py', 'run.py', 'server.py', 
            'manage.py', 'start.py', '__main__.py'
        ]
        
        # 检查虚拟环境
        venv_paths = ['venv', '.venv', 'env', '.env']
        python_cmd = "python"
        for venv in venv_paths:
            if (path / venv).exists():
                if os.name == 'nt':  # Windows
                    python_cmd = f"{venv}\\Scripts\\python.exe"
                else:  # Unix/Linux/Mac
                    python_cmd = f"{venv}/bin/python"
                break
        
        # 检查是否需要安装依赖
        install_cmd = ""
        if (path / "requirements.txt").exists():
            install_cmd = "pip install -r requirements.txt"
        elif (path / "setup.py").exists():
            install_cmd = "pip install -e ."
        elif (path / "pyproject.toml").exists():
            install_cmd = "pip install -e ."
        
        # 查找入口文件
        for entry_file in entry_candidates:
            if (path / entry_file).exists():
                start_cmd = f"{python_cmd} {entry_file}"
                return self._combine_commands(install_cmd, start_cmd)
        
        # Django项目检测
        if (path / "manage.py").exists():
            start_cmd = f"{python_cmd} manage.py runserver"
            return self._combine_commands(install_cmd, start_cmd)
            
        # Flask应用检测
        for py_file in path.glob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'Flask' in content and 'app.run' in content:
                        start_cmd = f"{python_cmd} {py_file.name}"
                        return self._combine_commands(install_cmd, start_cmd)
            except:
                pass
        
        # 默认尝试
        start_cmd = f"{python_cmd} app.py"
        return self._combine_commands(install_cmd, start_cmd)
    
    def _detect_java_maven_launch_command(self, path: Path) -> str:
        """检测Java Maven项目启动命令"""
        # Spring Boot项目
        pom_path = path / "pom.xml"
        try:
            with open(pom_path, 'r', encoding='utf-8') as f:
                pom_content = f.read()
                if 'spring-boot' in pom_content.lower():
                    return "mvn spring-boot:run"
        except:
            pass
        
        return "mvn exec:java"
    
    def _detect_java_gradle_launch_command(self, path: Path) -> str:
        """检测Java Gradle项目启动命令"""
        # Spring Boot项目
        gradle_files = list(path.glob("build.gradle*"))
        for gradle_file in gradle_files:
            try:
                with open(gradle_file, 'r', encoding='utf-8') as f:
                    gradle_content = f.read()
                    if 'spring-boot' in gradle_content.lower():
                        return "./gradlew bootRun" if os.name != 'nt' else "gradlew.bat bootRun"
            except:
                pass
        
        return "./gradlew run" if os.name != 'nt' else "gradlew.bat run"
    
    def _detect_go_launch_command(self, path: Path) -> str:
        """检测Go项目启动命令"""
        # 检查main.go文件
        if (path / "main.go").exists():
            return "go run main.go"
        
        # 检查cmd目录（常见的Go项目结构）
        cmd_dir = path / "cmd"
        if cmd_dir.exists():
            for subdir in cmd_dir.iterdir():
                if subdir.is_dir() and (subdir / "main.go").exists():
                    return f"go run cmd/{subdir.name}/main.go"
        
        return "go run ."