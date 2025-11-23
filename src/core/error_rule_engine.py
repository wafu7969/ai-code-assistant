"""
ErrorRuleEngine 模块

提供基于规则的错误检测和修复引擎。
"""
import re
from typing import List, Dict, Callable

class ErrorRuleEngine:
    """基于规则的错误检测和修复引擎"""

    def __init__(self):
        self.rules: List[Dict[str, Callable]] = []

    def add_rule(self, pattern: str, fix: Callable[[str], str]):
        """
        添加错误检测规则

        Args:
            pattern: 错误匹配的正则表达式
            fix: 修复函数，接受错误字符串并返回修复建议
        """
        self.rules.append({"pattern": pattern, "fix": fix})

    def detect_errors(self, log: str) -> List[str]:
        """
        从日志中检测错误

        Args:
            log: 日志内容

        Returns:
            检测到的错误列表
        """
        errors = []
        for rule in self.rules:
            matches = re.findall(rule["pattern"], log)
            errors.extend(matches)
        return errors

    def suggest_fixes(self, errors: List[str]) -> List[str]:
        """
        根据错误生成修复建议

        Args:
            errors: 错误列表

        Returns:
            修复建议列表
        """
        suggestions = []
        for error in errors:
            for rule in self.rules:
                if re.search(rule["pattern"], error):
                    suggestions.append(rule["fix"](error))
        return suggestions