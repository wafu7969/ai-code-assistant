"""
文件操作工具模块

提供安全的文件读写操作
"""
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from ..utils.path_utils import PathUtils
from ..utils.validators import Validators


class FileOperations:
    """文件操作工具类"""
    
    # 项目扫描时要忽略的目录
    IGNORE_DIRS = {
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
    
    def __init__(self, root: Optional[str] = None, output_dir: str = "output"):
        """
        初始化文件操作工具
        
        Args:
            root: 项目根目录
            output_dir: 输出目录名称
        """
        self.path_utils = PathUtils(root)
        self.output_dir = output_dir
        
        # 确保输出目录存在
        output_path_obj = Path(output_dir)
        if output_path_obj.is_absolute():
            # 绝对路径，直接使用
            self.output_path = output_path_obj
        else:
            # 相对路径，基于项目根目录
            self.output_path = self.path_utils.base_dir / output_dir
        
        self.path_utils.ensure_dir_exists(self.output_path)
    
    def _resolve_file_path(self, file_path: str) -> Path:
        """
        解析文件路径，统一处理不同的路径格式
        
        Args:
            file_path: 输入的文件路径
            
        Returns:
            解析后的完整路径
            
        Raises:
            ValueError: 路径不安全时抛出
        """
        output_dir_name = Path(self.output_dir).name
        
        # 标准化路径分隔符进行比较
        normalized_file_path = str(file_path).replace("\\", "/")
        normalized_output_dir = str(self.output_path).replace("\\", "/")
        
        if normalized_file_path.startswith(normalized_output_dir + "/"):
            # 完整路径且在输出目录内，直接使用（跳过常规安全检查）
            return Path(file_path)
        elif str(file_path).startswith(output_dir_name + "/") or str(file_path).startswith(output_dir_name + "\\"):
            # 文件路径以输出目录名称开头，替换为完整路径
            relative_path = str(file_path)[len(output_dir_name) + 1:]  # +1 去掉分隔符
            return self.output_path / relative_path
        else:
            # 相对路径，需要验证安全性
            if not self.path_utils.is_safe_path(file_path):
                raise ValueError("不安全的文件路径")
            return self.output_path / file_path
    
    def read_file(self, file_path: str) -> str:
        """
        安全读取文件内容
        
        Args:
            file_path: 相对文件路径
            
        Returns:
            文件内容或错误信息
        """
        try:
            # 使用统一的路径解析方法
            full_path = self._resolve_file_path(file_path)
        except ValueError as e:
            return f"错误: {str(e)}"
        
        try:
            
            if not full_path.exists():
                return "错误: 文件不存在"
            
            if not full_path.is_file():
                return "错误: 路径不是文件"
            
            # 读取文件内容
            content = full_path.read_text(encoding="utf-8")
            return content
            
        except PermissionError:
            return "错误: 没有文件读取权限"
        except UnicodeDecodeError:
            return "错误: 文件编码格式不支持"
        except Exception as e:
            return f"错误: {str(e)}"
    
    def write_file(self, file_path: str, content: str) -> str:
        """
        安全写入文件
        
        Args:
            file_path: 相对文件路径
            content: 文件内容
            
        Returns:
            操作结果
        """
        try:
            # 解析路径
            output_dir_name = Path(self.output_dir).name
            
            if str(file_path).startswith(self.output_dir + "/") or str(file_path).startswith(self.output_dir + "\\"):
                # 完整路径且在输出目录内，直接使用
                full_path = Path(file_path)
            elif str(file_path).startswith(output_dir_name + "/") or str(file_path).startswith(output_dir_name + "\\"):
                # 文件路径以输出目录名称开头，替换为完整路径
                relative_path = str(file_path)[len(output_dir_name) + 1:]
                full_path = self.output_path / relative_path
            else:
                # 相对路径，需要验证安全性
                if not self.path_utils.is_safe_path(file_path):
                    return "错误: 不安全的文件路径"
                full_path = self.output_path / file_path
            
            # 验证文件名
            if not Validators.is_valid_filename(full_path.name):
                return "错误: 无效的文件名"
            
            # 验证文件扩展名
            if not Validators.is_safe_file_extension(str(full_path)):
                return "错误: 不支持的文件类型"
            
            # 确保父目录存在
            self.path_utils.ensure_dir_exists(full_path.parent)
            
            # 写入文件
            full_path.write_text(content, encoding="utf-8")
            
            return "成功"
            
        except PermissionError:
            return "错误: 没有文件写入权限"
        except OSError as e:
            return f"错误: 文件系统错误 - {str(e)}"
        except Exception as e:
            return f"错误: {str(e)}"
    
    def list_files(self, directory: str = "") -> List[str]:
        """
        列出目录中的文件
        
        Args:
            directory: 相对目录路径
            
        Returns:
            文件列表
        """
        try:
            if directory:
                if not self.path_utils.is_safe_path(directory):
                    return ["错误: 不安全的目录路径"]
                # 如果目录路径已经包含output目录，直接使用，否则添加到output目录下
                if str(directory).startswith(self.output_dir + "/") or str(directory).startswith(self.output_dir + "\\"):
                    dir_path = self.path_utils.safe_join(Path(directory))
                else:
                    dir_path = self.path_utils.safe_join(Path(self.output_dir) / directory)
            else:
                dir_path = self.output_path
            
            if not dir_path.exists():
                return []
            
            if not dir_path.is_dir():
                return ["错误: 路径不是目录"]
            
            files = []
            for item in dir_path.iterdir():
                if item.is_file():
                    # 返回相对于输出目录的路径
                    rel_path = item.relative_to(self.output_path)
                    files.append(str(rel_path))
            
            return sorted(files)
            
        except Exception as e:
            return [f"错误: {str(e)}"]
    
    def file_exists(self, file_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 相对文件路径
            
        Returns:
            文件是否存在
        """
        try:
            full_path = self._resolve_file_path(file_path)
            return full_path.exists() and full_path.is_file()
            
        except Exception:
            return False
    
    def delete_file(self, file_path: str) -> str:
        """
        删除文件
        
        Args:
            file_path: 相对文件路径
            
        Returns:
            操作结果
        """
        try:
            # 解析路径
            output_dir_name = Path(self.output_dir).name
            
            if str(file_path).startswith(self.output_dir + "/") or str(file_path).startswith(self.output_dir + "\\"):
                # 完整路径且在输出目录内，直接使用
                full_path = Path(file_path)
            elif str(file_path).startswith(output_dir_name + "/") or str(file_path).startswith(output_dir_name + "\\"):
                # 文件路径以输出目录名称开头，替换为完整路径
                relative_path = str(file_path)[len(output_dir_name) + 1:]
                full_path = self.output_path / relative_path
            else:
                # 相对路径，需要验证安全性
                if not self.path_utils.is_safe_path(file_path):
                    return "错误: 不安全的文件路径"
                full_path = self.output_path / file_path
            
            if not full_path.exists():
                return "错误: 文件不存在"
            
            if not full_path.is_file():
                return "错误: 路径不是文件"
            
            full_path.unlink()
            return "成功"
            
        except PermissionError:
            return "错误: 没有删除权限"
        except Exception as e:
            return f"错误: {str(e)}"
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件信息
        
        Args:
            file_path: 相对文件路径
            
        Returns:
            文件信息字典
        """
        try:
            # 解析路径
            output_dir_name = Path(self.output_dir).name
            
            if str(file_path).startswith(self.output_dir + "/") or str(file_path).startswith(self.output_dir + "\\"):
                # 完整路径且在输出目录内，直接使用
                full_path = Path(file_path)
            elif str(file_path).startswith(output_dir_name + "/") or str(file_path).startswith(output_dir_name + "\\"):
                # 文件路径以输出目录名称开头，替换为完整路径
                relative_path = str(file_path)[len(output_dir_name) + 1:]
                full_path = self.output_path / relative_path
            else:
                # 相对路径，需要验证安全性
                if not self.path_utils.is_safe_path(file_path):
                    return {"error": "不安全的文件路径"}
                full_path = self.output_path / file_path
            
            if not full_path.exists():
                return {"error": "文件不存在"}
            
            stat = full_path.stat()
            
            return {
                "name": full_path.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "is_file": full_path.is_file(),
                "is_dir": full_path.is_dir(),
                "extension": full_path.suffix
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def add_ignore_dirs(self, dirs: List[str]):
        """
        添加要忽略的目录名称
        
        Args:
            dirs: 要添加到忽略列表的目录名称列表
        """
        if isinstance(dirs, str):
            dirs = [dirs]
        self.IGNORE_DIRS.update(dirs)
    
    def remove_ignore_dirs(self, dirs: List[str]):
        """
        从忽略列表中移除目录名称
        
        Args:
            dirs: 要从忽略列表中移除的目录名称列表
        """
        if isinstance(dirs, str):
            dirs = [dirs]
        for dir_name in dirs:
            self.IGNORE_DIRS.discard(dir_name)
    
    def get_project_tree(self, target_path: str = "output", max_depth: int = 10, include_hidden: bool = False, 
                        custom_ignore: Optional[List[str]] = None) -> str:
        """
        获取项目目录树状结构，默认获取output目录
        
        Args:
            target_path: 目标路径，默认为"output"目录
            max_depth: 最大递归深度
            include_hidden: 是否包含隐藏文件/目录
            custom_ignore: 本次扫描临时忽略的目录列表
            
        Returns:
            树状结构字符串
        """
        try:
            if target_path:
                # 特殊处理：如果是"."，直接使用项目根目录
                if target_path == "." or target_path == "./":
                    base_path = self.path_utils.base_dir
                # 如果是相对路径，优先在项目根目录查找
                elif target_path == "output" or target_path.startswith("output"):
                    # 直接使用output目录的绝对路径
                    base_path = self.output_path
                    if target_path != "output":
                        # 如果是output的子目录
                        sub_path = target_path.replace("output/", "").replace("output\\", "")
                        base_path = base_path / sub_path
                else:
                    # 其他路径处理
                    # 检查是否在项目根目录内
                    potential_path = self.path_utils.base_dir / target_path
                    if potential_path.exists():
                        # 如果在项目根目录内存在，直接使用
                        base_path = potential_path
                    else:
                        # 特殊处理：如果请求的路径名和输出目录名相同，直接使用输出目录
                        output_dir_name = Path(self.output_dir).name
                        if target_path == output_dir_name:
                            base_path = self.output_path
                        else:
                            # 如果不存在，检查是否安全再尝试在output目录中查找
                            if not self.path_utils.is_safe_path(target_path):
                                return "错误: 不安全的路径"
                            
                            # 尝试在 output 目录中查找
                            base_path = self.output_path / target_path
            else:
                # 空字符串默认扫描output目录
                base_path = self.output_path
            
            if not base_path.exists():
                return f"错误: 路径不存在 - {target_path or '项目根目录'}"
            
            if not base_path.is_dir():
                return f"错误: 路径不是目录 - {target_path or '项目根目录'}"
            
            # 生成树状结构
            tree_lines = []
            tree_lines.append(f"📁 {base_path.name or '项目根目录'}/")
            
            # 准备忽略目录集合
            ignore_dirs = self.IGNORE_DIRS.copy()
            if custom_ignore:
                ignore_dirs.update(custom_ignore)
            
            self._build_tree_recursive(
                base_path, 
                tree_lines, 
                prefix="", 
                depth=0, 
                max_depth=max_depth,
                include_hidden=include_hidden,
                ignore_dirs=ignore_dirs
            )
            
            return "\n".join(tree_lines)
            
        except Exception as e:
            return f"错误: {str(e)}"
    
    def _build_tree_recursive(self, path: Path, tree_lines: List[str], prefix: str, 
                            depth: int, max_depth: int, include_hidden: bool, ignore_dirs: set):
        """
        递归构建目录树
        
        Args:
            path: 当前路径
            tree_lines: 树状结构行列表
            prefix: 当前行的前缀
            depth: 当前深度
            max_depth: 最大深度
            include_hidden: 是否包含隐藏文件
            ignore_dirs: 要忽略的目录集合
        """
        if depth >= max_depth:
            return
        
        try:
            # 获取目录内容
            items = []
            for item in path.iterdir():
                # 跳过隐藏文件/目录（除非明确包含）
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                # 跳过忽略目录
                if item.is_dir() and (item.name in ignore_dirs or item.name.endswith('.egg-info')):
                    continue
                    
                items.append(item)
            
            # 排序：目录在前，文件在后，然后按名称排序
            items.sort(key=lambda x: (x.is_file(), x.name.lower()))
            
            for i, item in enumerate(items):
                is_last = (i == len(items) - 1)
                
                # 决定当前项的连接符
                connector = "└── " if is_last else "├── "
                
                # 决定图标
                if item.is_dir():
                    icon = "📁"
                    name = f"{item.name}/"
                else:
                    icon = self._get_file_icon(item.suffix)
                    name = item.name
                
                # 添加到树状结构
                tree_lines.append(f"{prefix}{connector}{icon} {name}")
                
                # 如果是目录，递归处理
                if item.is_dir() and depth + 1 < max_depth:
                    # 计算下一级的前缀
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    self._build_tree_recursive(
                        item, 
                        tree_lines, 
                        next_prefix, 
                        depth + 1, 
                        max_depth,
                        include_hidden,
                        ignore_dirs
                    )
                    
        except PermissionError:
            tree_lines.append(f"{prefix}└── ❌ 权限不足")
        except Exception as e:
            tree_lines.append(f"{prefix}└── ⚠️ 错误: {str(e)}")
    
    def _get_file_icon(self, extension: str) -> str:
        """
        根据文件扩展名获取图标
        
        Args:
            extension: 文件扩展名
            
        Returns:
            文件图标
        """
        icon_map = {
            '.py': '🐍',
            '.js': '📜',
            '.ts': '📘',
            '.html': '🌐',
            '.css': '🎨',
            '.json': '📋',
            '.md': '📝',
            '.txt': '📄',
            '.yml': '⚙️',
            '.yaml': '⚙️',
            '.xml': '📄',
            '.sql': '🗄️',
            '.sh': '🔧',
            '.bat': '🔧',
            '.exe': '⚡',
            '.zip': '📦',
            '.tar': '📦',
            '.gz': '📦',
            '.jpg': '🖼️',
            '.jpeg': '🖼️',
            '.png': '🖼️',
            '.gif': '🖼️',
            '.svg': '🖼️',
            '.pdf': '📕',
            '.doc': '📘',
            '.docx': '📘',
            '.xls': '📗',
            '.xlsx': '📗'
        }
        
        return icon_map.get(extension.lower(), '📄')


def build_file_tools(root: Optional[str] = None, output_dir: str = "output") -> List:
    """
    构建文件操作工具列表
    
    Args:
        root: 项目根目录
        output_dir: 输出目录
        
    Returns:
        工具列表
    """
    file_ops = FileOperations(root, output_dir)
    
    try:
        from langchain_core.tools import Tool
    except ImportError:
        try:
            from langchain.tools import Tool
        except ImportError:
            return []
    
    def read_file_tool(input_str: str) -> str:
        """读取文件工具函数"""
        path = str(input_str).strip()
        return file_ops.read_file(path)
    
    def write_file_tool(input_str: str) -> str:
        """写入文件工具函数"""
        try:
            data = json.loads(str(input_str))
            path = data.get("path", "").strip()
            content = data.get("content", "")
            return file_ops.write_file(path, content)
        except json.JSONDecodeError:
            # 检查是否是误将文件路径传给write_file工具
            input_clean = str(input_str).strip()
            if not input_clean.startswith("{") and not input_clean.endswith("}"):
                return f"错误: write_file工具需要JSON格式输入，如果要读取文件 '{input_clean}'，请使用read_file工具"
            return "错误: 无效的JSON格式，write_file工具需要格式: {\"path\": \"文件路径\", \"content\": \"文件内容\"}"
        except Exception as e:
            return f"错误: {str(e)}"
    
    def get_project_tree_tool(input_str: str) -> str:
        """获取项目树状结构工具函数"""
        try:
            if not input_str.strip():
                # 默认参数
                return file_ops.get_project_tree()
            
            # 尝试解析JSON参数
            data = json.loads(str(input_str))
            target_path = data.get("path", "")
            max_depth = data.get("max_depth", 3)
            include_hidden = data.get("include_hidden", False)
            
            return file_ops.get_project_tree(target_path, max_depth, include_hidden)
        except json.JSONDecodeError:
            # 如果不是JSON，当作路径处理
            return file_ops.get_project_tree(str(input_str).strip())
        except Exception as e:
            return f"错误: {str(e)}"
    
    return [
        Tool(
            name="read_file",
            description="读取项目中文本文件内容，输入为相对路径字符串。",
            func=read_file_tool
        ),
        Tool(
            name="write_file",
            description="写入项目中文件，输入为JSON字符串: {path, content}。",
            func=write_file_tool
        ),
        Tool(
            name="get_project_tree",
            description="获取项目目录树状结构，默认获取output目录。输入为空字符串(默认output)或JSON: {path?, max_depth?, include_hidden?}。",
            func=get_project_tree_tool
        )
    ]