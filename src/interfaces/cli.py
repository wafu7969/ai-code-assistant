"""
命令行接口模块
提供用户交互的命令行界面
"""
import sys
from pathlib import Path
from typing import Optional

from ..core.app_context import get_app_context
from ..core.router import TaskRouter
from ..core.planner import ProjectPlanner
from ..core.executor import CodeExecutor
from ..core.question_handler import QuestionHandler
from ..models.task_types import TaskType
from ..utils.logger import setup_logging, enable_logging, get_logger
from ..utils.ui_helpers import UIHelpers


class CLI:
    """命令行接口类"""
    
    def __init__(self):
        """
        初始化CLI
        """
        # 获取项目配置管理器（使用环境变量配置的项目路径）
        self.context = get_app_context()
        self.root = self.context.root
        
        # 获取输出目录配置
        output_dir = self.context.get_output_directory()
        
        # 初始化日志系统
        self.logger = setup_logging("ai_assistant", "logs")
        enable_logging()  # 替换print函数
        
        # 初始化核心组件
        self.router = TaskRouter(self.root)                    # 任务路由器：智能分析用户输入，识别任务类型（简单开发/复杂开发/Bug修复/问答）
        self.planner = ProjectPlanner(self.root)               # 项目计划器：将复杂任务拆分为2-6个可执行步骤
        self.executor = CodeExecutor(self.root, output_dir)    # 代码执行器：负责实际的代码生成、文件操作和项目启动
        self.question_handler = QuestionHandler(root=self.root, output_dir=output_dir)  # 问题解答器：处理技术咨询和使用指导
        
        print("🤖 AI代码助手已启动")
        UIHelpers.show_welcome_message()
    

    
    def run(self):
        """运行CLI主循环"""
        while True:
            try:
                # 获取用户输入 只能单行输入
                user_input = input("\n🗣️ 请输入你的需求（或输入 'exit' 退出，'help' 查看帮助）：\n> ").strip()
                
                if not user_input:
                    continue
                
                # 处理特殊命令
                if user_input.lower() == "exit":
                    print("\n👋 再见！感谢使用AI代码助手")
                    print("📝 所有对话记录已保存到logs目录")
                    from ..utils.logger import disable_logging
                    disable_logging()  # 恢复原始print函数
                    break
                elif user_input.lower() == "help":
                    UIHelpers.show_help()
                    continue
                elif user_input.lower() == "status":
                    UIHelpers.show_system_status(self.router, self.executor, self.root)
                    continue
                
                # 处理用户任务
                self._process_user_task(user_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 用户中断，退出程序")
                break
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
                print("请重试或输入 'help' 查看帮助")
    
    def _process_user_task(self, user_input: str):
        """
        处理用户任务
        Args:
            user_input: 用户输入
        """
        try:
            # 记录原始用户输入
            self.logger.info(f"\n🗒️ 用户输入: {user_input}")

            # 路由任务
            self.logger.debug("\n🔍 正在分析任务类型...")
            task = self.router.route_task(user_input)
            
            self.logger.info(f"🎯 路由结果 - 任务类型: {UIHelpers.get_task_type_description(task.task_type)}, 任务内容: {task.content}")
            
            # 根据任务类型处理
            if task.task_type == TaskType.DEV_SIMPLE:   # 简单开发任务
                self.logger.debug("🚀 进入简单开发任务处理流程")
                self._handle_simple_development(task)
            elif task.task_type == TaskType.DEV_COMPLEX:
                self.logger.debug("🚀 进入复杂开发任务处理流程")
                self._handle_complex_development(task)
            elif task.task_type == TaskType.BUG_FIX:
                self.logger.debug("🐛 进入Bug修复任务处理流程")
                self._handle_bug_fix(task)
            elif task.task_type == TaskType.QUESTION_ANSWER:
                self.logger.debug("💬 进入问题解答任务处理流程")
                self._handle_question_answer(task)
            else:
                self.logger.warning("\n❓ 未能识别的任务类型，默认按简单开发处理")
                self._handle_simple_development(task)
                
        except ValueError as e:
            self.logger.error(f"\n❌ 输入验证失败: {e}")
        except Exception as e:
            self.logger.error(f"\n❌ 处理任务时出错: {e}")
    
    def _handle_simple_development(self, task):
        """处理简单开发任务"""
        print("\n🚀 开始简单开发模式（智能分析+直接生成）...")
        
        # 先扫描项目信息
        print("🔍 正在扫描现有项目结构...")
        project_context = UIHelpers.scan_project_context(self.root)
        
        step = {
            "title": "智能开发",
            "detail": f"基于现有项目结构分析需求并生成代码: {task.content}"
        }
        
        print("⚙️ 正在分析需求并生成代码...")
        result = self.executor.execute_step(task.content, step, project_context)
        
        print("\n🛠️ 开发完成！")
        print("📄 执行结果:")
        print("-" * 40)
        print(result)
        print("-" * 40)
        output_dir = self.context.get_output_directory()
        print(f"\n📁 生成的文件保存在: {output_dir}/ 目录")
        
        # 询问用户是否启动项目
        launch_confirm = input("\n❓ 是否启动生成的项目进行测试？(y/n): ").strip().lower()
        if launch_confirm in ['y', 'yes', '是']:
            self._launch_project()
    
    def _handle_complex_development(self, task):
        """处理复杂开发任务"""
        print("\n📋 开始复杂开发模式（智能规划+逐步执行）...")
        
        # 先扫描项目信息
        print("🔍 正在分析现有项目结构...")
        project_context = UIHelpers.scan_project_context(self.root)
        
        # 基于项目上下文创建计划
        print("🧠 正在基于项目分析制定开发计划...")
        steps = self.planner.create_plan(task.content, project_context)
        
        print(f"\n📝 开发计划（共{len(steps)}个步骤）:")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step['title']}")
            print(f"     {step['detail']}")
        
        # 让用户确认是否执行
        confirm = input("\n❓ 是否开始执行计划？(y/n): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("⏸️ 计划制定完成，等待用户确认执行")
            return
        
        # 执行计划
        print("\n🚀 开始执行开发计划...")
        history = ""
        
        for i, step in enumerate(steps, 1):
            print(f"\n📍 执行第{i}步: {step['title']}")
            print(f"   详情: {step['detail']}")
            print("   ⚙️ 处理中...")
            
            result = self.executor.execute_step(task.content, step, history)
            
            print(f"   ✅ 第{i}步完成")
            history += f"\n\n第{i}步 {step['title']}\n{result}"
        
        print("\n🎉 所有步骤执行完成！")
        output_dir = self.context.get_output_directory()
        print(f"📁 生成的文件保存在: {output_dir}/ 目录")
        
        # 询问用户是否启动项目
        launch_confirm = input("\n❓ 是否启动生成的项目进行测试？(y/n): ").strip().lower()
        if launch_confirm in ['y', 'yes', '是']:
            self._launch_project()
    
    def _handle_bug_fix(self, task):
        """处理Bug修复任务"""
        print("\n🐛 开始Bug修复模式...")
        print("💡 提示：Bug修复将分析问题并提供解决方案")
        
        # 先扫描项目信息
        print("\n🔍 正在分析现有项目结构...")
        project_context = UIHelpers.scan_project_context(self.root)
        
        # 分析Bug信息
        print("🔍 正在分析Bug信息...")
        
        # 构建Bug修复的执行步骤
        step = {
            "title": "Bug分析与修复",
            "detail": f"分析并修复Bug: {task.content}"
        }
        
        print("🔧 正在生成修复方案...")
        result = self.executor.execute_step(task.content, step, project_context)
        
        print("\n🛠️ Bug修复完成！")
        print("📄 修复结果:")
        print("-" * 40)
        print(result)
        print("-" * 40)
        output_dir = self.context.get_output_directory()
        print(f"\n📁 修复的文件保存在: {output_dir}/ 目录")
        print("💡 建议：请检查修复结果并进行测试验证")
    
    def _handle_question_answer(self, task):
        """处理问题解答任务"""
        print("\n💬 开始问题解答模式...")
        print("🤖 AI助手将智能分析您的问题，自动判断是否需要读取项目文件...")
        
        try:
            # 使用简化的问题处理器
            answer = self.question_handler.handle_question(task.content)
            
            print("\n" + "="*60)
            print("📄 问题解答结果:")
            print("="*60)
            print(answer)
            print("="*60)
            
        except Exception as e:
            print(f"❌ 问题解答失败: {e}")
            print("💡 建议：请重新描述您的问题，或检查问题是否清晰明确")
    
    def _launch_project(self):
        """启动生成的项目"""
        print("\n🚀 启动项目...")
        try:
            result = self.executor.launch_and_test_project()
            print(f"📄 启动结果: {result}")
        except Exception as e:
            print(f"❌ 启动项目时发生错误: {e}")


def main():
    """主函数"""
    try:
        cli = CLI()
        cli.run()
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()