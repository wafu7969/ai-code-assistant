"""
项目检测服务

提供统一的项目检测逻辑，支持多种项目类型的识别和启动命令生成。
"""
from pathlib import Path
from typing import Dict, Any

class ProjectDetector:
    """统一的项目检测服务"""

    def detect_project_type(self, path: Path) -> str:
        """
        检测项目类型

        Args:
            path: 项目路径

        Returns:
            项目类型字符串
        """
        # 优先检测配置文件
        if (path / "package.json").exists():
            return "Node.js"
        elif (path / "requirements.txt").exists() or (path / "setup.py").exists():
            return "Python"
        elif (path / "pom.xml").exists():
            return "Java-Maven"
        elif (path / "build.gradle").exists():
            return "Java-Gradle"
        elif (path / "go.mod").exists():
            return "Go"
        elif (path / "Cargo.toml").exists():
            return "Rust"
        elif (path / "composer.json").exists():
            return "PHP"
        
        # 检测HTML/静态文件
        elif (path / "index.html").exists():
            return "Static"
        
        # 智能检测：基于文件扩展名
        else:
            files = list(path.glob("*"))
            
            # 检测Python项目
            if any(f.suffix == ".py" for f in files):
                return "Python"
            
            # 检测JavaScript/Node.js项目
            elif any(f.suffix in [".js", ".jsx", ".ts", ".tsx"] for f in files):
                return "Node.js"
            
            # 检测Java项目
            elif any(f.suffix == ".java" for f in files):
                return "Java-Maven"
            
            # 检测Go项目
            elif any(f.suffix == ".go" for f in files):
                return "Go"
            
            # 检测Rust项目
            elif any(f.suffix == ".rs" for f in files):
                return "Rust"
            
            # 检测PHP项目
            elif any(f.suffix == ".php" for f in files):
                return "PHP"
            
            # 检测静态Web项目
            elif any(f.suffix in [".html", ".htm", ".css"] for f in files):
                return "Static"
            
            # 默认未知
            else:
                return "Unknown"

    def generate_launch_command(self, path: Path, project_type: str) -> str:
        """
        根据项目类型生成启动命令

        Args:
            path: 项目路径
            project_type: 项目类型

        Returns:
            启动命令字符串
        """
        if project_type == "Node.js":
            return "npm install && npm run dev"
        elif project_type == "Python":
            return "pip install -r requirements.txt && python main.py"
        elif project_type == "Java-Maven":
            return "mvn spring-boot:run"
        elif project_type == "Java-Gradle":
            return "./gradlew bootRun"
        elif project_type == "Go":
            return "go run main.go"
        elif project_type == "Rust":
            return "cargo run"
        elif project_type == "PHP":
            return "composer install && php artisan serve"
        elif project_type == "Static":
            return "python -m http.server"
        else:
            # 未知项目类型时，尝试智能检测并提供合理的默认命令
            if (path / "index.html").exists():
                return "python -m http.server 8000"
            elif (path / "main.py").exists():
                return "python main.py"
            elif (path / "app.py").exists():
                return "python app.py"
            elif any((path / f).exists() for f in ["server.js", "index.js", "main.js"]):
                return "node index.js"
            else:
                return "python -m http.server 8000"  # 默认启动静态服务器

    def detect_and_generate(self, path: Path) -> Dict[str, Any]:
        """
        综合检测项目类型并生成启动命令

        Args:
            path: 项目路径

        Returns:
            包含项目类型和启动命令的字典
        """
        project_type = self.detect_project_type(path)
        launch_command = self.generate_launch_command(path, project_type)
        return {
            "project_type": project_type,
            "launch_command": launch_command
        }