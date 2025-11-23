"""
UI界面辅助工具模块

提供CLI界面相关的辅助函数
"""
from pathlib import Path
from typing import Optional
from ..models.task_types import TaskType


class UIHelpers:
    """UI辅助工具类"""
    
    @staticmethod
    def show_welcome_message():
        """显示欢迎信息"""
        print("\n" + "="*60)
        print("🎯 支持的任务类型:")
        print("  📄 简单开发: 单个页面、组件、函数等")
        print("  🏗️  复杂开发: 完整系统、多模块项目等")
        print("  🐛 Bug修复: 错误修复、性能优化等")
        print("  💬 问题解答: 技术咨询、使用指导等")
        print("\n🚀 智能特性:")
        print("  • 自动识别任务复杂度")
        print("  • 简单任务直接开发，复杂任务拆分计划")
        print("  • 安全的文件操作和路径管理")
        print("  • 内置Git版本控制支持")
        print("="*60)
    
    @staticmethod
    def show_help():
        """显示帮助信息"""
        help_text = """
🆘 AI代码助手帮助信息

📋 命令列表:
  help   - 显示此帮助信息
  status - 显示系统状态
  exit   - 退出程序

🎯 任务类型:
  
  📄 简单开发任务
    • 单个页面或组件 (如：开发一个登录页)
    • 单个功能模块 (如：创建一个搜索框)
    • 简单工具函数 (如：写一个数据验证函数)
    
  🏗️ 复杂开发任务
    • 完整系统 (如：开发一个OA办公系统)
    • 多模块项目 (如：用户管理+权限+报表系统)
    • 需要架构设计的项目
    
  🐛 Bug修复任务
    • 修复程序错误
    • 性能优化
    • 代码重构
    
  💬 问题解答任务
    • 技术咨询
    • 使用指导
    • 概念解释

💡 使用技巧:
  • 描述需求时请尽量详细和具体
  • 复杂项目会自动拆分为多个步骤执行
  • 简单任务会直接生成代码，提高效率
  • 所有生成的文件都保存在配置的输出目录下

📞 获取更多帮助:
  • GitHub: https://github.com/your-org/ai-code-assistant
  • 文档: docs/ 目录
        """
        print(help_text)
    
    @staticmethod
    def get_task_type_description(task_type: TaskType) -> str:
        """获取任务类型描述"""
        descriptions = {
            TaskType.DEV_SIMPLE: "简单开发任务",
            TaskType.DEV_COMPLEX: "复杂开发任务", 
            TaskType.BUG_FIX: "Bug修复任务",
            TaskType.QUESTION_ANSWER: "问题解答任务"
        }
        return descriptions.get(task_type, "未知任务类型")
    
    @staticmethod
    def scan_project_context(root_path: str) -> str:
        """扫描项目上下文信息"""
        try:
            from pathlib import Path
            from .project_helpers import ProjectHelpers
            
            context_info = []
            
            # 1. 扫描项目根目录结构
            context_info.append("项目结构分析 ===")
            
            # 获取项目根目录的文件和文件夹
            root_path = Path(root_path)
            
            # 获取配置的输出目录
            project_helper = ProjectHelpers(str(root_path))
            output_dir_name = project_helper.get_output_directory()
            
            # 处理输出目录路径：绝对路径直接使用，相对路径基于项目根目录
            output_dir_path = Path(output_dir_name)
            if output_dir_path.is_absolute():
                output_path = output_dir_path
            else:
                output_path = root_path / output_dir_name
            
            if output_path.exists():
                context_info.append(f"\n=== {output_dir_name.title()} 目录内容 ===")
                # 定义要忽略的目录和文件（基于FileOperations.IGNORE_DIRS）
                ignore_dirs = {
                    # Python相关
                    '__pycache__', '.pytest_cache', 'venv', 'env', '.venv', '.env',
                    'site-packages', 'build', 'dist',
                    
                    # Node.js相关
                    'node_modules', 'bower_components', '.npm', '.yarn',
                    
                    # 版本控制
                    '.git', '.svn', '.hg', '.bzr',
                    
                    # IDE相关
                    '.vscode', '.idea', '.vs', '.eclipse', '.sublime-project',
                    
                    # 系统文件
                    '.DS_Store', 'Thumbs.db', 'Desktop.ini',
                    
                    # 临时文件
                    'tmp', 'temp', '.tmp', '.temp', 'cache', '.cache',
                    
                    # 编译产物
                    'target', 'bin', 'obj', 'out',
                    
                    # 日志文件
                    'logs', 'log', '.log',
                    
                    # 其他框架相关
                    '.next', '.nuxt', 'coverage', '.coverage', '.nyc_output'
                }
                
                ignore_files = {
                    # 锁定文件
                    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
                    'Pipfile.lock', 'poetry.lock', 'composer.lock',
                    
                    # 系统和临时文件
                    '.DS_Store', 'Thumbs.db', 'Desktop.ini',
                    
                    # 编译和缓存文件
                    '*.pyc', '*.pyo', '*.class', '*.o', '*.so'
                }
                
                output_files = []
                for item in output_path.iterdir():
                    # 跳过隐藏文件（除了重要的配置文件）
                    if item.name.startswith('.') and item.name not in {'.env.example', '.gitignore', '.github'}:
                        continue
                    
                    # 跳过忽略的目录和文件
                    if item.name in ignore_dirs or item.name in ignore_files:
                        continue
                    
                    if item.is_file():
                        output_files.append(f"📄 {item.name}")
                    elif item.is_dir():
                        output_files.append(f"📁 {item.name}/")
                
                if output_files:
                    context_info.append(f"{output_dir_name.title()}目录现有文件:")
                    context_info.extend([f"  {file}" for file in output_files[:80]])
                    if len(output_files) > 80:
                        context_info.append(f"  ... 还有 {len(output_files) - 80} 个文件")
                else:
                    context_info.append(f"{output_dir_name.title()}目录为空")
            else:
                context_info.append(f"\n=== {output_dir_name.title()} 目录 ===")
                context_info.append(f"{output_dir_name.title()}目录不存在，将创建新目录")
            
            return "\n".join(context_info)
            
        except Exception as e:
            return f"项目扫描失败: {str(e)}"
    
    @staticmethod
    def show_system_status(router, executor, root_path: str):
        """显示系统状态"""
        print("\n📊 系统状态:")
        
        # 检查路由器状态
        router_status = router.get_router_status()
        print(f"  🔍 任务路由器: {'正常' if router_status['llm_available'] else '异常'}")
        
        # 检查LLM状态
        model_info = router_status['model_info']
        print(f"  🤖 大语言模型: {model_info.get('status', '未知')}")
        
        if model_info.get('status') == '已加载':
            print(f"      模型: {model_info.get('model_name', '未知')}")
            print(f"      API: {model_info.get('base_url', '未知')}")
        
        # 检查工具状态
        tools = executor.get_tools()
        print(f"  🛠️ 可用工具: {len(tools)} 个")
        for tool in tools:
            print(f"      - {tool.name}")
        
        # 检查输出目录
        from .project_helpers import ProjectHelpers
        project_helper = ProjectHelpers(root_path)
        output_dir_name = project_helper.get_output_directory()
        
        # 处理输出目录路径：绝对路径直接使用，相对路径基于项目根目录
        output_dir_path = Path(output_dir_name)
        if output_dir_path.is_absolute():
            output_path = output_dir_path
        else:
            output_path = Path(root_path) / output_dir_name
        print(f"  📁 输出目录: {output_path}")
        print(f"      状态: {'存在' if output_path.exists() else '不存在'}")