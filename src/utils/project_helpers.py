"""
项目辅助工具模块

提供项目管理相关的辅助函数
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from .config_loader import ConfigLoader


class ProjectHelpers:
    """项目辅助工具类"""
    
    def __init__(self, root: Optional[str] = None):
        """
        初始化项目辅助工具
        
        Args:
            root: 项目根目录
        """
        self.root = root or str(Path.cwd())
        self.config_loader = ConfigLoader(Path(self.root))
    
    def get_output_directory(self) -> str:
        """
        获取输出目录路径
        
        Returns:
            输出目录路径
        """
        # 优先从环境变量读取
        output_dir = os.getenv("OUTPUT_DIR")
        
        if not output_dir:
            # 从配置文件读取
            env_config = self.config_loader.load_env_config()
            output_dir = env_config.get("OUTPUT_DIR", "output")
        
        # 如果没有配置，使用默认值
        if not output_dir:
            output_dir = "output"
        
        return output_dir
    
    def get_project_config(self) -> Dict[str, Any]:
        """
        获取项目配置
        
        Returns:
            项目配置字典
        """
        # 加载环境变量配置
        env_config = self.config_loader.load_env_config()
        
        # 基础配置
        config = {
            "project_root": self.root,
            "output_dir": self.get_output_directory(),
            "debug": env_config.get("DEBUG", "false").lower() == "true",
            "log_level": env_config.get("LOG_LEVEL", "INFO"),
        }
        
        # LLM配置
        config["llm"] = {
            "openrouter_api_key": env_config.get("OPENROUTER_API_KEY"),
            "openrouter_base_url": env_config.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            "openrouter_model": env_config.get("OPENROUTER_MODEL", "anthropic/claude-3-5-sonnet"),
            "openai_api_key": env_config.get("OPENAI_API_KEY"),
            "openai_model": env_config.get("OPENAI_MODEL", "gpt-4"),
        }
        
        return config
    
    def ensure_output_directory(self) -> Path:
        """
        确保输出目录存在
        
        Returns:
            输出目录路径对象
        """
        output_dir = self.get_output_directory()
        
        # 处理输出目录路径：绝对路径直接使用，相对路径基于项目根目录
        output_dir_path = Path(output_dir)
        if output_dir_path.is_absolute():
            output_path = output_dir_path
        else:
            output_path = Path(self.root) / output_dir
            
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path
    
    def create_default_env_file(self):
        """创建默认的.env文件（如果不存在）"""
        env_path = Path(self.root) / ".env"
        
        if not env_path.exists():
            template_path = Path(self.root) / "config" / ".env.template"
            if template_path.exists():
                # 复制模板文件
                import shutil
                shutil.copy2(template_path, env_path)
                print(f"✅ 已创建 .env 文件，请编辑配置")
            else:
                # 创建基本的.env文件
                default_content = """# AI代码助手环境变量配置
# OpenRouter API配置 (推荐)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=anthropic/claude-3-5-sonnet

# 项目配置
PROJECT_ROOT=.
OUTPUT_DIR=output

# 开发配置
DEBUG=false
LOG_LEVEL=INFO
"""
                env_path.write_text(default_content, encoding='utf-8')
                print(f"✅ 已创建默认 .env 文件，请编辑配置")
    
    def validate_environment(self) -> Dict[str, Any]:
        """
        验证环境配置
        
        Returns:
            验证结果字典
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        config = self.get_project_config()
        
        # 检查API密钥
        if not config["llm"]["openrouter_api_key"] and not config["llm"]["openai_api_key"]:
            result["errors"].append("缺少API密钥配置 (OPENROUTER_API_KEY 或 OPENAI_API_KEY)")
            result["valid"] = False
        
        # 检查输出目录
        output_path = Path(self.root) / config["output_dir"]
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            result["errors"].append(f"无法创建输出目录: {e}")
            result["valid"] = False
        
        # 检查项目根目录权限
        if not os.access(self.root, os.W_OK):
            result["warnings"].append("项目根目录可能没有写入权限")
        
        return result