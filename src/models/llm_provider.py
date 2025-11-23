"""
LLM提供者模块

负责大语言模型的配置、加载和管理
基于原 agent/llm.py 重构
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from ..utils.config_loader import ConfigLoader


class LLMProvider:
    """大语言模型提供者"""
    
    def __init__(self, root: Optional[str] = None):
        """
        初始化LLM提供者
        
        Args:
            root: 项目根目录路径
        """
        self.root = Path(root) if root else Path.cwd()
        self.config_loader = ConfigLoader(self.root)
        self._model = None
    
    def load_model(self) -> Optional[Any]:
        """
        加载LLM模型
        
        Returns:
            加载的模型实例，失败时返回None
        """
        if self._model is not None:
            return self._model
            
        try:
            # 加载环境变量配置
            env_config = self._load_environment_config()
            
            # 获取模型配置参数
            base_url = env_config.get(
                "OPENROUTER_BASE_URL", 
                os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            )
            
            api_key = env_config.get(
                "OPENROUTER_API_KEY", 
                os.getenv("OPENROUTER_API_KEY", os.getenv("OPENAI_API_KEY", ""))
            )
            
            model_name = env_config.get(
                "OPENROUTER_MODEL", 
                os.getenv("OPENROUTER_MODEL", os.getenv("OPENAI_MODEL", "anthropic/claude-3-5-sonnet"))
            )
            
            if not api_key:
                print("警告: 未找到API密钥，请检查环境变量配置")
                return None
            
            # 导入并创建模型
            from langchain_openai import ChatOpenAI
            self._model = ChatOpenAI(
                api_key=api_key,
                base_url=base_url,
                model=model_name,
                temperature=0
            )
            
            return self._model
            
        except Exception as e:
            print(f"加载LLM模型失败: {e}")
            return None
    
    def _load_environment_config(self) -> Dict[str, str]:
        """
        加载环境变量配置
        
        Returns:
            环境变量字典
        """
        env_config = {}
        dotenv_path = self.root / ".env"
        
        if not dotenv_path.exists():
            return env_config
            
        try:
            content = dotenv_path.read_text(encoding="utf-8")
        except Exception:
            return env_config
            
        # 解析.env文件
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
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        model = self.load_model()
        if model is None:
            return {"status": "未加载", "error": "模型加载失败"}
            
        return {
            "status": "已加载",
            "model_name": getattr(model, 'model_name', 'unknown'),
            "base_url": getattr(model, 'base_url', 'unknown'),
            "temperature": getattr(model, 'temperature', 'unknown')
        }