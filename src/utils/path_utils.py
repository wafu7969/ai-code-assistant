"""
路径工具模块

提供安全的路径操作功能
"""
from pathlib import Path
from typing import Union, Optional


class PathUtils:
    """路径工具类"""
    
    def __init__(self, base_dir: Optional[Union[str, Path]] = None):
        """
        初始化路径工具
        
        Args:
            base_dir: 基础目录，默认为当前工作目录
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.base_dir = self.base_dir.resolve()
    
    def safe_join(self, path: Union[str, Path], allow_absolute: bool = False) -> Path:
        """
        安全地连接路径，防止目录遍历攻击
        
        Args:
            path: 要连接的路径
            allow_absolute: 是否允许绝对路径（用于输出目录配置等场景）
            
        Returns:
            安全的绝对路径
            
        Raises:
            ValueError: 当路径不安全时
        """
        if isinstance(path, str):
            path = Path(path)
            
        # 如果是绝对路径
        if path.is_absolute():
            if not allow_absolute:
                raise ValueError(f"不允许使用绝对路径: {path}")
            # 对于允许的绝对路径，直接返回解析后的路径
            return path.resolve()
        
        # 解析路径并检查是否在基础目录内
        resolved_path = (self.base_dir / path).resolve()
        
        # 检查解析后的路径是否在基础目录内
        try:
            resolved_path.relative_to(self.base_dir)
        except ValueError:
            raise ValueError(f"路径超出了允许的范围: {path}")
            
        return resolved_path
    
    def ensure_dir_exists(self, path: Union[str, Path], parents: bool = True) -> Path:
        """
        确保目录存在，如不存在则创建
        
        Args:
            path: 目录路径
            parents: 是否创建父目录
            
        Returns:
            目录路径
        """
        if isinstance(path, str):
            path = Path(path)
            
        path.mkdir(parents=parents, exist_ok=True)
        return path
    
    def get_relative_path(self, path: Union[str, Path]) -> Path:
        """
        获取相对于基础目录的相对路径
        
        Args:
            path: 绝对路径或相对路径
            
        Returns:
            相对路径
        """
        if isinstance(path, str):
            path = Path(path)
            
        if path.is_absolute():
            try:
                return path.relative_to(self.base_dir)
            except ValueError:
                # 路径不在基础目录内
                return path
        else:
            return path
    
    def is_safe_path(self, path: Union[str, Path]) -> bool:
        """
        检查路径是否安全
        
        Args:
            path: 要检查的路径
            
        Returns:
            路径是否安全
        """
        try:
            self.safe_join(path)
            return True
        except ValueError:
            return False
    
    def get_output_path(self, relative_path: Union[str, Path] = "", output_dir_name: str = "output") -> Path:
        """
        获取输出目录路径
        
        Args:
            relative_path: 相对于输出目录的路径
            output_dir_name: 输出目录名称
            
        Returns:
            输出路径
        """
        output_dir = self.base_dir / output_dir_name
        self.ensure_dir_exists(output_dir)
        
        if relative_path:
            return self.safe_join(Path(output_dir_name) / relative_path)
        return output_dir
    
    def normalize_path(self, path: Union[str, Path]) -> str:
        """
        标准化路径格式
        
        Args:
            path: 原始路径
            
        Returns:
            标准化后的路径字符串
        """
        if isinstance(path, str):
            path = Path(path)
            
        # 统一使用正斜杠
        return str(path).replace('\\', '/')