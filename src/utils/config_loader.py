"""
配置加载器

负责加载和管理项目配置
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """配置加载器类"""
    
    def __init__(self, root: Optional[Path] = None):
        """
        初始化配置加载器
        
        Args:
            root: 项目根目录
        """
        self.root = root or Path.cwd()
        self._config_cache = {}
    
    def load_yaml_config(self, config_path: str = "config/default.yaml") -> Dict[str, Any]:
        """
        加载YAML配置文件
        
        Args:
            config_path: 配置文件相对路径
            
        Returns:
            配置字典
        """
        if config_path in self._config_cache:
            return self._config_cache[config_path]
            
        full_path = self.root / config_path
        
        if not full_path.exists():
            print(f"配置文件不存在: {full_path}")
            return {}
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                self._config_cache[config_path] = config
                return config
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}
    
    def load_env_config(self, env_file: str = ".env") -> Dict[str, str]:
        """
        加载环境变量配置
        
        Args:
            env_file: 环境变量文件名
            
        Returns:
            环境变量字典
        """
        env_path = self.root / env_file
        env_config = {}
        
        if not env_path.exists():
            return env_config
            
        try:
            content = env_path.read_text(encoding="utf-8")
        except Exception:
            return env_config
            
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            if line.startswith("export "):
                line = line[len("export "):].strip()
                
            if "=" not in line:
                continue
                
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            
            if key:
                env_config[key] = value
                
        return env_config
    
    def get_config_value(self, key: str, default: Any = None, 
                        config_file: str = "config/default.yaml") -> Any:
        """
        获取配置值，支持点号分隔的嵌套键
        
        Args:
            key: 配置键，支持 "section.subsection.key" 格式
            default: 默认值
            config_file: 配置文件路径
            
        Returns:
            配置值
        """
        config = self.load_yaml_config(config_file)
        
        keys = key.split(".")
        value = config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def clear_cache(self):
        """清除配置缓存"""
        self._config_cache.clear()