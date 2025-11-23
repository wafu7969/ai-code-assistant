"""
任务类型定义模块

定义系统支持的任务类型和复杂度分级
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class TaskType(Enum):
    """任务类型枚举"""
    DEV_SIMPLE = "dev_simple"      # 简单开发任务
    DEV_COMPLEX = "dev_complex"    # 复杂开发任务
    BUG_FIX = "bug"               # Bug修复
    QUESTION_ANSWER = "qa"         # 问题解答


class TaskComplexity(Enum):
    """任务复杂度枚举"""
    SIMPLE = "simple"      # 简单任务
    MEDIUM = "medium"      # 中等复杂度
    COMPLEX = "complex"    # 复杂任务


@dataclass
class Task:
    """任务数据模型"""
    content: str                           # 任务内容
    task_type: TaskType                    # 任务类型
    complexity: TaskComplexity             # 复杂度
    description: Optional[str] = None      # 任务描述
    
    @classmethod
    def create_simple_dev_task(cls, content: str) -> "Task":
        """创建简单开发任务"""
        return cls(
            content=content,
            task_type=TaskType.DEV_SIMPLE,
            complexity=TaskComplexity.SIMPLE,
            description="简单开发任务，直接执行"
        )
    
    @classmethod
    def create_complex_dev_task(cls, content: str) -> "Task":
        """创建复杂开发任务"""
        return cls(
            content=content,
            task_type=TaskType.DEV_COMPLEX,
            complexity=TaskComplexity.COMPLEX,
            description="复杂开发任务，需要拆分计划"
        )