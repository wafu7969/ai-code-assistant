"""
项目配置管理器

提供统一的项目级别组件管理，避免重复初始化
使用单例模式确保全局唯一实例
"""
from pathlib import Path
from typing import Optional, Dict, Any
from ..utils.config_loader import ConfigLoader
from ..utils.path_utils import PathUtils
from ..utils.project_helpers import ProjectHelpers


class AppContext:
    """统一的项目配置管理器"""
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """
        单例模式创建实例
            
        Returns:
            AppContext 实例
        """
        if cls._instance is None:
            cls._instance = super(AppContext, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        初始化项目配置管理器
        
        使用环境变量配置确定项目根目录
        """
        # 防止重复初始化
        if self._initialized:
            return
            
        # 优先从环境变量读取项目根目录
        self.root = self._get_project_root()
        self.root_path = Path(self.root).resolve()
        
        # 初始化核心组件
        self._initialize_core_components()
        
        # 缓存常用配置
        self._config_cache = {}
        
        self._initialized = True
    
    def _get_project_root(self) -> str:
        """
        获取项目根目录
        
        优先级:
        1. 系统环境变量 PROJECT_ROOT
        2. .env文件中的 PROJECT_ROOT
        3. 当前工作目录
        
        Returns:
            项目根目录路径
        """
        import os
        
        # 1. 优先从系统环境变量读取
        project_root = os.getenv("PROJECT_ROOT")
        if project_root:
            return str(Path(project_root).resolve())
        
        # 2. 从.env文件读取
        try:
            # 临时使用当前目录创建ConfigLoader来读取配置
            temp_config_loader = ConfigLoader(Path.cwd())
            env_config = temp_config_loader.load_env_config()
            project_root = env_config.get("PROJECT_ROOT")
            if project_root:
                # 如果是相对路径，相对于当前工作目录解析
                if not Path(project_root).is_absolute():
                    return str((Path.cwd() / project_root).resolve())
                return str(Path(project_root).resolve())
        except Exception:
            pass
        
        # 3. 默认使用当前工作目录
        return str(Path.cwd())
    
    def _initialize_core_components(self):
        """初始化核心组件"""
        try:
            # 配置加载器
            self.config_loader = ConfigLoader(self.root_path)
            
            # 路径工具
            self.path_utils = PathUtils(self.root_path)
            
            # 项目辅助工具
            self.project_helper = ProjectHelpers(self.root)
            
            # 加载项目配置
            self.project_config = self.project_helper.get_project_config()
            
        except Exception as e:
            print(f"警告: 项目配置管理器初始化部分失败: {e}")
            # 设置默认值确保系统可以继续运行
            self.config_loader = None
            self.path_utils = None
            self.project_helper = None
            self.project_config = {}
    
    def get_output_directory(self) -> str:
        """
        获取输出目录路径
        
        Returns:
            输出目录路径
        """
        if self.project_helper:
            return self.project_helper.get_output_directory()
        
        # fallback 默认值
        return "output"
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持缓存
        
        Args:
            key: 配置键，支持点号分隔
            default: 默认值
            
        Returns:
            配置值
        """
        if key in self._config_cache:
            return self._config_cache[key]
            
        if self.config_loader:
            value = self.config_loader.get_config_value(key, default)
        else:
            value = default
            
        self._config_cache[key] = value
        return value
    
    def get_env_config(self) -> Dict[str, Any]:
        """
        获取环境变量配置
        
        Returns:
            环境变量配置字典
        """
        if self.config_loader:
            return self.config_loader.load_env_config()
        return {}
    
    def clear_cache(self):
        """清除配置缓存"""
        self._config_cache.clear()
        if self.config_loader:
            self.config_loader.clear_cache()
    
    def get_status_info(self) -> Dict[str, Any]:
        """
        获取项目配置管理器状态信息
        
        Returns:
            状态信息字典
        """
        return {
            "root_path": str(self.root_path),
            "output_directory": self.get_output_directory(),
            "config_loaded": self.config_loader is not None,
            "project_helper_loaded": self.project_helper is not None,
            "cache_size": len(self._config_cache)
        }
    
    @classmethod
    def reset_instance(cls):
        """重置实例（主要用于测试）"""
        cls._instance = None
        cls._initialized = False


# 提供全局访问函数
def get_app_context() -> AppContext:
    """
    获取项目配置管理器实例
    
    Returns:
        AppContext 实例
    """
    return AppContext()