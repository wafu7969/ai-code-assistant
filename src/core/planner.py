"""
项目计划器模块

负责将复杂任务拆分为可执行的步骤
"""
import json
import re
from typing import List, Dict, Any, Optional
from ..models.llm_provider import LLMProvider
from ..models.task_types import Task
from ..utils.validators import Validators


class ProjectPlanner:
    """项目计划器"""
    
    def __init__(self, root: Optional[str] = None):
        """
        初始化项目计划器
        
        Args:
            root: 项目根目录
        """
        self.llm_provider = LLMProvider(root)
    
    def create_plan(self, task_content: str, project_context: str = "") -> List[Dict[str, str]]:
        """
        创建项目计划
        
        Args:
            task_content: 任务内容
            project_context: 项目上下文信息
            
        Returns:
            步骤列表
        """
        model = self.llm_provider.load_model()
        
        if model is None:
            raise RuntimeError("LLM模型未正确加载，无法创建项目计划")
        
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        
        # 构建包含项目上下文的提示
        context_section = ""
        if project_context:
            context_section = """       
                **当前项目分析结果：**
                """ + project_context + """

                **重要指导：**
                - 基于上述项目分析结果制定计划
                - 考虑现有技术栈和项目结构
                - 如果是在现有系统基础上扩展，要考虑集成和兼容性
                - 重用现有的代码风格、组件、工具函数
                - 保持与现有项目的一致性
            """
        
        system_prompt = """
            你是资深的软件工程开发助手，请基于项目分析结果将用户需求拆解为2-6个可执行步骤。
            """ + context_section + """

            **拆分要求：**
            - 只返回一个 JSON 数组，不要任何额外文本
            - 每个步骤任务要独立、单一，步骤之间不能有重叠
            - 能合并的任务要合并，不要刻意拆分
            - 数组元素为对象，且仅包含两个键：title、detail
            - 步骤按执行顺序排列
            - **如果有现有项目上下文，第一步通常应该是分析现有相关代码**
            
            **拆分步骤的错误示例：**
            - 错误的：第一步创建登录页面；第二步给登录页面添加输入校验；第三步优化登录页面加载性能；
            - 正确的：生成一个登录页面，要求：对输入进行校验、优化页面加载性能

            **基于项目上下文的示例：**
            [
              {{"title": "分析现有相关代码", "detail": "读取并分析现有的用户管理、页面结构等相关代码"}},
              {{"title": "扩展现有功能", "detail": "基于现有代码风格和架构添加新功能，需要添加新功能的入口点（如：超级链接、路由、API接口等）"}},
              {{"title": "集成测试", "detail": "确保新功能与现有系统的兼容性"}}
            ]
            """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}\n\n请基于项目分析结果返回 JSON数组。")
        ])
        
        chain = prompt | model | StrOutputParser()
        raw_response = chain.invoke({"input": task_content}).strip()
        
        return self._parse_plan_response(raw_response)
    
    def _parse_plan_response(self, raw_response: str) -> List[Dict[str, str]]:
        """
        解析LLM返回的计划响应
        
        Args:
            raw_response: 原始响应
            
        Returns:
            解析后的步骤列表
        """
        # 提取JSON部分
        json_text = raw_response
        if not json_text.startswith("["):
            # 尝试提取JSON数组
            match = re.search(r'\[.*\]', json_text, re.DOTALL)
            if match:
                json_text = match.group(0)
            else:
                raise ValueError("未找到有效的JSON数组")
        
        # 解析JSON
        steps_data = json.loads(json_text)
        
        if not isinstance(steps_data, list):
            raise ValueError("响应不是数组格式")
        
        # 验证和清理步骤
        validated_steps = []
        for i, step_data in enumerate(steps_data):
            if not isinstance(step_data, dict):
                continue
            
            # 验证步骤数据
            errors = Validators.validate_step_data(step_data)
            if errors:
                print(f"步骤 {i+1} 验证失败: {errors}")
                continue
            
            step = {
                "title": step_data.get("title", f"步骤{i+1}").strip(),
                "detail": step_data.get("detail", "执行该步骤").strip()
            }
            
            validated_steps.append(step)
        
        # 如果没有有效步骤，抛出异常
        if not validated_steps:
            raise ValueError("LLM返回的计划无效，没有可用的步骤")
        
        return validated_steps
    
    def validate_plan(self, steps: List[Dict[str, str]]) -> List[str]:
        """
        验证计划的有效性
        
        Args:
            steps: 步骤列表
            
        Returns:
            错误信息列表
        """
        errors = []
        
        if not steps:
            errors.append("计划不能为空")
            return errors
        
        if len(steps) > 10:
            errors.append("计划步骤过多，建议控制在10步以内")
        
        for i, step in enumerate(steps):
            step_errors = Validators.validate_step_data(step)
            for error in step_errors:
                errors.append(f"步骤 {i+1}: {error}")
        
        return errors
    
    def optimize_plan(self, steps: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        优化计划步骤
        
        Args:
            steps: 原始步骤列表
            
        Returns:
            优化后的步骤列表
        """
        if not steps:
            return steps
        
        optimized = []
        
        for step in steps:
            # 清理和优化步骤内容
            title = step.get("title", "").strip()
            detail = step.get("detail", "").strip()
            
            # 跳过空步骤
            if not title and not detail:
                continue
            
            # 设置默认值
            if not title:
                title = f"步骤{len(optimized) + 1}"
            if not detail:
                detail = "执行该步骤"
            
            optimized.append({
                "title": title[:100],  # 限制标题长度
                "detail": detail[:500]  # 限制详情长度
            })
        
        return optimized