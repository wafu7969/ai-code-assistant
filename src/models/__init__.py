"""
模型层

包含LLM提供者和数据模型：
- LLM配置和加载
- 任务类型定义
- 数据模型
"""

from .llm_provider import LLMProvider
from .task_types import TaskType, TaskComplexity

__all__ = ["LLMProvider", "TaskType", "TaskComplexity"]