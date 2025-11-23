"""
Git操作工具模块

提供Git版本控制操作
"""
import json
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from ..utils.path_utils import PathUtils
from ..utils.validators import Validators


class GitOperations:
    """Git操作工具类"""
    
    def __init__(self, root: Optional[str] = None, output_dir: str = "output"):
        """
        初始化Git操作工具
        
        Args:
            root: 项目根目录
            output_dir: 输出目录名称
        """
        self.path_utils = PathUtils(root)
        self.output_dir = output_dir
        
        # 处理绝对路径和相对路径
        output_path_obj = Path(output_dir)
        if output_path_obj.is_absolute():
            # 绝对路径，直接使用
            self.repo_path = output_path_obj
        else:
            # 相对路径，基于项目根目录
            self.repo_path = self.path_utils.base_dir / output_dir
        
        # 确保输出目录存在
        self.path_utils.ensure_dir_exists(self.repo_path)
    
    def is_git_available(self) -> bool:
        """
        检查Git是否可用
        
        Returns:
            Git是否可用
        """
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                cwd=str(self.repo_path)
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def is_git_repo(self) -> bool:
        """
        检查是否为Git仓库
        
        Returns:
            是否为Git仓库
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True,
                cwd=str(self.repo_path)
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def init_repo(self) -> str:
        """
        初始化Git仓库
        
        Returns:
            操作结果
        """
        try:
            if not self.is_git_available():
                return "错误: Git不可用"
            
            if self.is_git_repo():
                return "Git仓库已存在"
            
            result = subprocess.run(
                ["git", "init"],
                capture_output=True,
                text=True,
                cwd=str(self.repo_path)
            )
            
            if result.returncode == 0:
                return "成功: Git仓库已初始化"
            else:
                return f"错误: {result.stderr}"
                
        except Exception as e:
            return f"错误: {str(e)}"
    
    def add_files(self, files: Optional[List[str]] = None, add_all: bool = True) -> str:
        """
        添加文件到暂存区
        
        Args:
            files: 文件列表，None表示使用add_all参数
            add_all: 是否添加所有文件
            
        Returns:
            操作结果
        """
        try:
            if not self.is_git_available():
                return "错误: Git不可用"
            
            if not self.is_git_repo():
                # 自动初始化Git仓库
                init_result = self.init_repo()
                if init_result.startswith("错误"):
                    return f"添加文件: {init_result}"
            
            if add_all or files is None:
                result = subprocess.run(
                    ["git", "add", "-A"],
                    capture_output=True,
                    text=True,
                    cwd=str(self.repo_path)
                )
            else:
                # 验证文件路径
                safe_files = []
                for file_path in files:
                    if self.path_utils.is_safe_path(file_path):
                        safe_files.append(file_path)
                
                if not safe_files:
                    return "错误: 没有有效的文件路径"
                
                result = subprocess.run(
                    ["git", "add"] + safe_files,
                    capture_output=True,
                    text=True,
                    cwd=str(self.repo_path)
                )
            
            if result.returncode == 0:
                return "成功: 文件已添加到暂存区"
            else:
                return f"错误: {result.stderr}"
                
        except Exception as e:
            return f"错误: {str(e)}"
    
    def commit(self, message: str, author: Optional[str] = None) -> str:
        """
        提交更改
        
        Args:
            message: 提交信息
            author: 作者信息
            
        Returns:
            操作结果
        """
        try:
            if not self.is_git_available():
                return "错误: Git不可用"
            
            if not self.is_git_repo():
                # 自动初始化Git仓库
                init_result = self.init_repo()
                if init_result.startswith("错误"):
                    return f"提交: {init_result}"
            
            if not message.strip():
                return "错误: 提交信息不能为空"
            
            # 检查提交信息长度
            if len(message) > 200:
                return "错误: 提交信息长度不能超过200个字符"
            
            # 先设置默认用户信息（如果没有设置的话）
            try:
                subprocess.run(
                    ["git", "config", "user.name", "AI Assistant"],
                    capture_output=True,
                    cwd=str(self.repo_path),
                    check=False  # 不检查返回码，因为可能已经设置
                )
                subprocess.run(
                    ["git", "config", "user.email", "ai@assistant.local"],
                    capture_output=True,
                    cwd=str(self.repo_path),
                    check=False
                )
            except:
                pass  # 忽略设置失败
            
            cmd = ["git", "commit", "-m", message]
            if author:
                cmd.extend(["--author", author])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.repo_path)
            )
            
            if result.returncode == 0:
                return f"成功: 提交完成 - {result.stdout.strip()}"
            else:
                return f"错误: {result.stderr}"
                
        except Exception as e:
            return f"错误: {str(e)}"
    
    def push(self, remote: str = "origin", branch: Optional[str] = None) -> str:
        """
        推送到远程仓库
        
        Args:
            remote: 远程仓库名称
            branch: 分支名称
            
        Returns:
            操作结果
        """
        try:
            if not self.is_git_available():
                return "错误: Git不可用"
            
            if not self.is_git_repo():
                return "错误: 不是Git仓库"
            
            # 获取当前分支
            if branch is None:
                branch_result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True,
                    text=True,
                    cwd=str(self.repo_path)
                )
                
                if branch_result.returncode == 0:
                    branch = branch_result.stdout.strip()
                else:
                    return "错误: 无法获取当前分支"
            
            result = subprocess.run(
                ["git", "push", remote, branch],
                capture_output=True,
                text=True,
                cwd=str(self.repo_path)
            )
            
            if result.returncode == 0:
                return f"成功: 推送到 {remote}/{branch}"
            else:
                return f"错误: {result.stderr}"
                
        except Exception as e:
            return f"错误: {str(e)}"
    
    def get_status(self) -> str:
        """
        获取Git状态
        
        Returns:
            状态信息
        """
        try:
            if not self.is_git_available():
                return "Git不可用"
            
            if not self.is_git_repo():
                return "不是Git仓库"
            
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=str(self.repo_path)
            )
            
            if result.returncode == 0:
                if result.stdout.strip():
                    return f"有未提交的更改:\n{result.stdout}"
                else:
                    return "工作目录干净"
            else:
                return f"错误: {result.stderr}"
                
        except Exception as e:
            return f"错误: {str(e)}"
    
    def full_commit_and_push(
        self, 
        message: str,
        files: Optional[List[str]] = None,
        add_all: bool = True,
        push_to_remote: bool = False,
        remote: str = "origin",
        branch: Optional[str] = None,
        dry_run: bool = False
    ) -> str:
        """
        完整的提交和推送流程
        
        Args:
            message: 提交信息
            files: 要添加的文件列表
            add_all: 是否添加所有文件
            push_to_remote: 是否推送到远程
            remote: 远程仓库名称
            branch: 分支名称
            dry_run: 是否只是预演
            
        Returns:
            操作结果
        """
        results = []
        
        if dry_run:
            plan = []
            if add_all:
                plan.append("git add -A")
            else:
                if files:
                    for file_path in files:
                        plan.append(f"git add {file_path}")
            plan.append(f"git commit -m \"{message}\"")
            if push_to_remote:
                target_branch = branch or "当前分支"
                plan.append(f"git push {remote} {target_branch}")
            
            return "预演模式 - 将执行的命令:\n" + "\n".join(plan)
        
        # 添加文件
        add_result = self.add_files(files, add_all)
        results.append(f"添加文件: {add_result}")
        
        if not add_result.startswith("成功"):
            return "\n".join(results)
        
        # 提交
        commit_result = self.commit(message)
        results.append(f"提交: {commit_result}")
        
        if not commit_result.startswith("成功"):
            return "\n".join(results)
        
        # 推送（可选）
        if push_to_remote:
            push_result = self.push(remote, branch)
            results.append(f"推送: {push_result}")
        
        return "\n".join(results)


def build_git_tools(root: Optional[str] = None, output_dir: str = "output") -> List:
    """
    构建 Git操作工具列表
    
    Args:
        root: 项目根目录
        output_dir: 输出目录
        
    Returns:
        工具列表
    """
    git_ops = GitOperations(root, output_dir)
    
    try:
        from langchain_core.tools import Tool
    except ImportError:
        try:
            from langchain.tools import Tool
        except ImportError:
            return []
    
    def git_commit_tool(input_str: str) -> str:
        """Git提交工具函数"""
        try:
            data = json.loads(str(input_str))
            
            # 验证数据
            errors = Validators.validate_git_commit_data(data)
            if errors:
                return f"错误: {'; '.join(errors)}"
            
            message = data.get("message", "").strip()
            files = data.get("paths", [])
            add_all = data.get("add_all", True)
            push_to_remote = data.get("push", False)
            remote = data.get("remote", "origin")
            branch = data.get("branch")
            dry_run = data.get("dry_run", False)
            
            return git_ops.full_commit_and_push(
                message=message,
                files=files if files else None,
                add_all=add_all,
                push_to_remote=push_to_remote,
                remote=remote,
                branch=branch,
                dry_run=dry_run
            )
            
        except json.JSONDecodeError:
            return "错误: 无效的JSON格式"
        except Exception as e:
            return f"错误: {str(e)}"
    
    return [
        Tool(
            name="git_commit",
            description="提交Git更改，输入JSON: {message, paths?, add_all?, push?, remote?, branch?, dry_run?}",
            func=git_commit_tool
        )
    ]