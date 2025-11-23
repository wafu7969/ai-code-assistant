"""
验证器模块

提供各种数据验证功能
"""
import re
import json
from pathlib import Path
from typing import Any, List, Dict, Optional


class Validators:
    """验证器类"""
    
    @staticmethod
    def is_valid_filename(filename: str) -> bool:
        """
        验证文件名是否有效
        
        Args:
            filename: 文件名
            
        Returns:
            是否有效
        """
        if not filename or len(filename.strip()) == 0:
            return False
            
        # 检查非法字符
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            if char in filename:
                return False
                
        # 检查保留名称
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in reserved_names:
            return False
            
        return True
    
    @staticmethod
    def is_valid_json(json_string: str) -> bool:
        """
        验证JSON字符串是否有效
        
        Args:
            json_string: JSON字符串
            
        Returns:
            是否有效
        """
        try:
            json.loads(json_string)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    @staticmethod
    def is_valid_task_content(content: str) -> bool:
        """
        验证任务内容是否有效
        
        Args:
            content: 任务内容
            
        Returns:
            是否有效
        """
        if not content or len(content.strip()) == 0:
            return False
            
        # 检查最小和最大长度
        content = content.strip()
        if len(content) < 5 or len(content) > 5000:
            return False
            
        return True
    
    @staticmethod
    def is_safe_file_extension(filename: str, allowed_extensions: Optional[List[str]] = None) -> bool:
        """
        验证文件扩展名是否安全
        
        Args:
            filename: 文件名
            allowed_extensions: 允许的扩展名列表
            
        Returns:
            是否安全
        """
        if allowed_extensions is None:
            # 默认允许的代码文件扩展名
            allowed_extensions = [
                # 基础代码文件
                '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.scss', '.less',
                '.json', '.yaml', '.yml', '.md', '.txt', '.xml', '.sql', '.sh', '.bat',
                
                # 现代JavaScript/TypeScript配置文件
                '.cjs', '.mjs', '.cts', '.mts', '.d.ts',
                
                # 构建和包管理配置
                '.toml', '.lock', '.log', '.csv', '.tsv',
                
                # 配置文件
                '.conf', '.config', '.ini', '.properties', '.env', '.dockerfile', 
                '.gitignore', '.gitattributes', '.editorconfig', '.dockerignore',
                '.prettierrc', '.eslintrc', '.babelrc', '.npmrc', '.nvmrc',
                
                # Vue和其他前端框架
                '.vue', '.svelte', '.astro',
                
                # Python包配置
                '.cfg', '.wheel', '.egg',
                
                # Java相关
                '.gradle', '.maven', '.pom',
                
                # 其他常用文件
                '.po', '.pot', '.mo', '.proto', '.graphql', '.gql',
                '.wasm', '.wat', '.webmanifest',
                
                # 允许无扩展名的配置文件
                ''
            ]
        
        file_path = Path(filename)
        file_ext = file_path.suffix.lower()
        file_name = file_path.name.lower()
        
        # 检查扩展名
        if file_ext in allowed_extensions:
            return True
            
        # 特殊检查常见的无扩展名配置文件
        special_files = {
            'dockerfile', 'makefile', 'rakefile', 'gemfile', 'procfile',
            'readme', 'changelog', 'license', 'authors', 'contributors',
            'nginx.conf', 'apache.conf', 'httpd.conf'
        }
        
        return file_name in special_files
    
    @staticmethod
    def validate_step_data(step: Dict[str, Any]) -> List[str]:
        """
        验证步骤数据格式
        
        Args:
            step: 步骤数据字典
            
        Returns:
            错误信息列表，空列表表示验证通过
        """
        errors = []
        
        # 检查必需字段
        required_fields = ['title', 'detail']
        for field in required_fields:
            if field not in step:
                errors.append(f"缺少必需字段: {field}")
            elif not isinstance(step[field], str) or len(step[field].strip()) == 0:
                errors.append(f"字段 {field} 必须是非空字符串")
        
        # 检查字段长度
        if 'title' in step and len(step['title']) > 100:
            errors.append("标题长度不能超过100个字符")
            
        if 'detail' in step and len(step['detail']) > 1000:
            errors.append("详情长度不能超过1000个字符")
            
        return errors
    
    @staticmethod
    def validate_git_commit_data(data: Dict[str, Any]) -> List[str]:
        """
        验证Git提交数据
        
        Args:
            data: Git提交数据
            
        Returns:
            错误信息列表
        """
        errors = []
        
        # 检查提交信息
        message = data.get('message', '').strip()
        if not message:
            errors.append("提交信息不能为空")
        elif len(message) > 200:
            errors.append("提交信息长度不能超过200个字符")
            
        # 检查路径列表
        paths = data.get('paths', [])
        if paths and not isinstance(paths, list):
            errors.append("paths 必须是数组类型")
            
        # 检查分支名
        branch = data.get('branch', '')
        if branch and not re.match(r'^[a-zA-Z0-9/_-]+$', branch):
            errors.append("分支名包含非法字符")
            
        return errors
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        清理用户输入，移除潜在的危险字符
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        if not isinstance(text, str):
            return str(text)
            
        # 移除控制字符
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # 限制长度
        if len(text) > 10000:
            text = text[:10000]
            
        return text.strip()