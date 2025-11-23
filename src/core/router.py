"""
任务路由器模块

负责智能分析用户输入，将任务路由到合适的处理流程
基于原 agent/router.py 重构
"""
from typing import Optional
from ..core.app_context import get_app_context
from ..models.llm_provider import LLMProvider
from ..models.task_types import TaskType, Task
from ..utils.validators import Validators


class TaskRouter:
    """任务路由器"""
    
    def __init__(self, root: Optional[str] = None):
        """
        初始化任务路由器
        
        Args:
            root: 项目根目录（已弃用，从AppContext自动获取）
        """
        self.context = get_app_context()
        # 使用AppContext提供的项目根目录
        self.llm_provider = LLMProvider(self.context.root)
        self._chain = None
        
        try:
            self._chain = self._build_router_chain()
        except Exception as e:
            print(f"路由器初始化失败: {e}")
            self._chain = None
    
    def route_task(self, user_input: str) -> Task:
        """
        路由用户任务
        
        Args:
            user_input: 用户输入
            
        Returns:
            任务对象
        """
        # 验证输入
        if not Validators.is_valid_task_content(user_input):
            raise ValueError("无效的任务内容")
        
        # 清理输入
        sanitized_input = Validators.sanitize_input(user_input)
        
        # 获取任务类型
        task_type_str = self._classify_task(sanitized_input)
        
        # 创建任务对象
        return self._create_task(sanitized_input, task_type_str)
    
    def _classify_task(self, user_input: str) -> str:
        """
        分类任务类型
        
        Args:
            user_input: 用户输入
            
        Returns:
            任务类型字符串
        """
        if self._chain is None:
            raise RuntimeError("LLM模型未正确加载，无法进行任务分类")
        
        result = self._chain.invoke({"input": user_input})
        return result.strip()
    

    
    def _create_task(self, user_input: str, task_type_str: str) -> Task:
        """
        创建任务对象
        
        Args:
            user_input: 用户输入
            task_type_str: 任务类型字符串
            
        Returns:
            任务对象
        """
        task_type = TaskType(task_type_str)
        
        if task_type == TaskType.DEV_SIMPLE:
            return Task.create_simple_dev_task(user_input)
        elif task_type == TaskType.DEV_COMPLEX:
            return Task.create_complex_dev_task(user_input)
        else:
            from ..models.task_types import TaskComplexity
            return Task(
                content=user_input,
                task_type=task_type,
                complexity=TaskComplexity.MEDIUM
            )
    
    def _build_router_chain(self):
        """
        构建路由链
        
        Returns:
            可调用的路由链
        """
        model = self.llm_provider.load_model()
        if not model:
            raise RuntimeError("LLM模型加载失败")
        
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        
        router_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            你是一个智能任务路由器，负责分析用户输入并分类到合适的任务类型。

            请根据以下规则进行精确分类：

            1. **简单开发任务** → 返回 "dev_simple"
               - 单个页面/组件（登录页、注册页、用户列表等）
               - 单个功能模块（搜索框、导航栏、表单等）
               - 简单的工具函数或配置文件
               - 单一文件的代码实现

            2. **复杂开发任务** → 返回 "dev_complex"  
               - 完整系统（OA系统、电商平台、管理系统等）
               - 多模块项目（用户管理+权限+报表等）
               - 需要多个页面协同的功能
               - 涉及数据库设计、架构设计的项目

            3. **Bug修复** → 返回 "bug"
               - 修复错误、调试问题、性能优化
               - 代码重构、错误排查
               - 功能异常修复

            4. **问题解答** → 返回 "qa"
               - 技术咨询、使用指导、概念解释
               - 询问如何实现某个功能
               - 学习相关的问题

            要求：只返回分类结果（dev_simple/dev_complex/bug/qa），不要任何额外解释或标点符号。
            """),
            ("human", "{input}")
        ])
        
        return router_prompt | model | StrOutputParser()
    
    def get_router_status(self) -> dict:
        """
        获取路由器状态
        
        Returns:
            状态信息字典
        """
        return {
            "llm_available": self._chain is not None,
            "model_info": self.llm_provider.get_model_info()
        }