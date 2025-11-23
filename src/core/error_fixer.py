"""
错误检测和修复模块

负责捕获项目中的错误并提供修复建议。
"""
import re
from typing import List, Tuple

class ErrorFixer:
    """错误检测和修复工具类"""

    def detect_errors(self, log: str) -> List[str]:
        """
        从日志中检测错误信息

        Args:
            log: 日志内容

        Returns:
            错误信息列表
        """
        error_patterns = [
            # Python 错误
            r"SyntaxError: .+",  # Python语法错误
            r"ModuleNotFoundError: .+",  # 模块未找到
            r"ImportError: .+",  # 导入错误
            r"FileNotFoundError: .+",  # 文件未找到
            r"PermissionError: .+",  # 权限错误
            r"ConnectionError: .+",  # 连接错误
            r"TimeoutError: .+",  # 超时错误
            r"OSError: .+",  # 系统错误
            
            # Node.js/JavaScript 错误
            r"Cannot find package '[^']+' imported from",  # Node.js包未找到
            r"Error \[ERR_MODULE_NOT_FOUND\]: Cannot find package '[^']+'",  # ES模块未找到
            r"Cannot resolve dependency: [^\\n]+",  # 依赖解析失败
            r"Module not found: Error: Can't resolve '[^']+'",  # Webpack模块未找到
            r"npm ERR! 404 Not Found",  # npm包不存在
            r"npm ERR! code ENOTFOUND",  # npm网络错误
            r"npm ERR! missing script:",  # npm脚本缺失
            r"failed to load config from .+",  # 配置文件加载失败
            r"Error: Cannot find module '[^']+'",  # CommonJS模块未找到
            
            # 系统错误
            r"Address already in use",  # 端口被占用
            r"Permission denied",  # 权限拒绝
            r"No such file or directory",  # 文件/目录不存在
            r"command not found",  # 命令未找到
            r"python: command not found",  # Python未找到
            r"npm: command not found",  # npm未找到
            r"node: command not found",  # node未找到
            r"yarn: command not found",  # yarn未找到
            
            # PowerShell 错误
            r"标记.*不是.*有效.*语句分隔符",  # PowerShell语法错误
            r"ParserError.*语句分隔符",  # PowerShell解析错误
            r"&&.*不是.*有效.*语句分隔符",  # 特定的&&错误
            r"Unexpected token.*&&",  # 意外的&&标记
            r"Port \d+ is already in use",  # 端口占用（英文版本）
            r"This package requires Node\.js version",  # Node.js版本要求
            
            # 通用错误
            r"Error: .+",  # 通用错误
            r"Exception: .+"  # 异常
        ]

        errors = []
        for pattern in error_patterns:
            matches = re.findall(pattern, log)
            errors.extend(matches)

        return errors

    def suggest_fixes(self, errors: List[str]) -> List[Tuple[str, str]]:
        """
        根据错误信息生成修复建议

        Args:
            errors: 错误信息列表

        Returns:
            修复建议列表，每个建议包含 (错误, 修复方案)
        """
        suggestions = []

        for error in errors:
            # Python 错误处理
            if "SyntaxError" in error:
                suggestions.append((error, "检查代码语法是否正确，确保括号和缩进匹配。"))
            elif "ModuleNotFoundError" in error or "ImportError" in error:
                module_name = re.search(r"'(.+?)'", error)
                if module_name:
                    module = module_name.group(1)
                    if module == "requests":
                        suggestions.append((error, "运行: pip install requests"))
                    elif module == "flask":
                        suggestions.append((error, "运行: pip install flask"))
                    elif module == "django":
                        suggestions.append((error, "运行: pip install django"))
                    else:
                        suggestions.append((error, f"尝试运行: pip install {module}"))
                else:
                    suggestions.append((error, "检查模块名称并使用 pip install 安装缺失的模块"))
            
            # Node.js 错误处理
            elif "Cannot find package" in error or "ERR_MODULE_NOT_FOUND" in error:
                # 提取包名
                package_match = re.search(r"Cannot find package '([^']+)'", error)
                if package_match:
                    package_name = package_match.group(1)
                    suggestions.append((error, f"运行: npm install {package_name}"))
                else:
                    suggestions.append((error, "运行: npm install 安装所有依赖"))
            elif "Cannot resolve dependency" in error:
                suggestions.append((error, "运行: npm install 或检查package.json中的依赖配置"))
            elif "Module not found" in error and "Can't resolve" in error:
                module_match = re.search(r"Can't resolve '([^']+)'", error)
                if module_match:
                    module_name = module_match.group(1)
                    suggestions.append((error, f"运行: npm install {module_name}"))
                else:
                    suggestions.append((error, "运行: npm install 安装缺失的模块"))
            elif "failed to load config" in error:
                if "vite.config" in error:
                    suggestions.append((error, "运行: npm install vite 或检查vite配置文件"))
                elif "webpack.config" in error:
                    suggestions.append((error, "运行: npm install webpack 或检查webpack配置文件"))
                else:
                    suggestions.append((error, "检查配置文件和相关依赖是否正确安装"))
            elif "npm ERR! missing script" in error:
                script_match = re.search(r"missing script: (\w+)", error)
                if script_match:
                    script_name = script_match.group(1)
                    suggestions.append((error, f"在package.json的scripts中添加'{script_name}'脚本"))
                else:
                    suggestions.append((error, "检查package.json中的scripts配置"))
            elif "npm ERR! 404 Not Found" in error:
                suggestions.append((error, "检查包名是否正确，或尝试清除npm缓存: npm cache clean --force"))
            elif "npm ERR! code ENOTFOUND" in error:
                suggestions.append((error, "检查网络连接，或配置npm镜像源"))
            
            # 系统错误处理
            elif "FileNotFoundError" in error or "No such file or directory" in error:
                suggestions.append((error, "检查文件路径是否正确，确保文件存在"))
            elif "PermissionError" in error or "Permission denied" in error:
                suggestions.append((error, "检查文件权限，尝试使用管理员权限运行"))
            elif "Address already in use" in error:
                suggestions.append((error, "端口已被占用，尝试使用其他端口或关闭占用该端口的程序"))
            elif "ConnectionError" in error:
                suggestions.append((error, "检查网络连接，确保目标服务可访问"))
            elif "TimeoutError" in error:
                suggestions.append((error, "连接超时，检查网络或增加超时时间"))
            elif "Port" in error and "is already in use" in error:
                port_match = re.search(r"Port (\d+) is already in use", error)
                if port_match:
                    port = port_match.group(1)
                    suggestions.append((error, f"端口{port}已被占用，尝试使用其他端口或关闭占用程序"))
                else:
                    suggestions.append((error, "端口已被占用，尝试使用其他端口或关闭占用该端口的程序"))
            
            # PowerShell 错误处理
            elif "标记" in error and "语句分隔符" in error:
                if "&&" in error:
                    suggestions.append((error, "PowerShell中不支持&&语法，请使用分号(;)分隔命令"))
                else:
                    suggestions.append((error, "PowerShell语法错误，请检查命令格式"))
            elif "ParserError" in error and "语句分隔符" in error:
                suggestions.append((error, "PowerShell解析错误，请使用正确的PowerShell语法"))
            elif "Unexpected token" in error and "&&" in error:
                suggestions.append((error, "在PowerShell中使用分号(;)而不是&&来连接命令"))
            elif "This package requires Node.js version" in error:
                version_match = re.search(r"requires Node\.js version ([^\\s]+)", error)
                if version_match:
                    required_version = version_match.group(1)
                    suggestions.append((error, f"需要Node.js版本{required_version}，请升级Node.js"))
                else:
                    suggestions.append((error, "Node.js版本不兼容，请升级Node.js版本"))
            
            # 命令未找到错误
            elif "python: command not found" in error:
                suggestions.append((error, "Python未安装或未添加到PATH，请安装Python"))
            elif "npm: command not found" in error:
                suggestions.append((error, "Node.js/npm未安装，请先安装Node.js"))
            elif "node: command not found" in error:
                suggestions.append((error, "Node.js未安装，请先安装Node.js"))
            elif "yarn: command not found" in error:
                suggestions.append((error, "Yarn未安装，运行: npm install -g yarn"))
            elif "command not found" in error:
                command = re.search(r"(\w+): command not found", error)
                if command:
                    suggestions.append((error, f"命令 '{command.group(1)}' 未找到，请检查是否已安装相应软件"))
                else:
                    suggestions.append((error, "命令未找到，检查命令是否正确或软件是否已安装"))
            
            # 通用错误处理
            elif "Error" in error or "Exception" in error:
                suggestions.append((error, "检查错误上下文并参考官方文档进行修复。"))
            else:
                suggestions.append((error, "无法提供具体建议，请手动检查。"))

        return suggestions

    def apply_fixes(self, suggestions: List[Tuple[str, str]]) -> str:
        """
        应用修复建议，尝试自动修复部分问题

        Args:
            suggestions: 修复建议列表
            
        Returns:
            修复结果信息
        """
        import subprocess
        import os
        
        print("\n🛠️ 修复建议:")
        results = []
        
        for error, fix in suggestions:
            print(f"- 错误: {error}")
            print(f"  修复方案: {fix}")
            
            # 尝试自动执行一些简单的修复
            auto_fix_attempted = False
            auto_fix_success = False
            
            # Node.js 依赖自动安装
            if "运行: npm install" in fix and "npm install" in fix:
                try:
                    print("  🔄 尝试自动执行修复...")
                    auto_fix_attempted = True
                    
                    # 提取具体的npm命令
                    if "npm install " in fix and not fix.endswith("npm install"):
                        # 有具体包名
                        cmd_start = fix.find("npm install")
                        cmd_part = fix[cmd_start:].split()[0:3]  # npm install package_name
                        if len(cmd_part) == 3:
                            cmd = " ".join(cmd_part)
                        else:
                            cmd = "npm install"
                    else:
                        cmd = "npm install"
                    
                    print(f"    执行: {cmd}")
                    result = subprocess.run(
                        cmd, 
                        shell=True, 
                        capture_output=True, 
                        text=True, 
                        timeout=60
                    )
                    
                    if result.returncode == 0:
                        print("  ✅ 自动修复成功!")
                        auto_fix_success = True
                        results.append(f"✅ 成功执行: {cmd}")
                    else:
                        print(f"  ❌ 自动修复失败: {result.stderr}")
                        results.append(f"❌ 执行失败: {cmd} - {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    print("  ⏱️ 修复超时，请手动执行")
                    results.append(f"⏱️ 超时: {cmd}")
                except Exception as e:
                    print(f"  ❌ 修复过程出错: {e}")
                    results.append(f"❌ 出错: {cmd} - {e}")
            
            # Python 依赖自动安装
            elif "运行: pip install" in fix:
                try:
                    print("  🔄 尝试自动执行修复...")
                    auto_fix_attempted = True
                    
                    # 提取pip命令
                    cmd_start = fix.find("pip install")
                    cmd_part = fix[cmd_start:].split()[0:3]  # pip install package_name
                    if len(cmd_part) == 3:
                        cmd = " ".join(cmd_part)
                    else:
                        cmd = "pip install"
                    
                    print(f"    执行: {cmd}")
                    result = subprocess.run(
                        cmd, 
                        shell=True, 
                        capture_output=True, 
                        text=True, 
                        timeout=60
                    )
                    
                    if result.returncode == 0:
                        print("  ✅ 自动修复成功!")
                        auto_fix_success = True
                        results.append(f"✅ 成功执行: {cmd}")
                    else:
                        print(f"  ❌ 自动修复失败: {result.stderr}")
                        results.append(f"❌ 执行失败: {cmd} - {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    print("  ⏱️ 修复超时，请手动执行")
                    results.append(f"⏱️ 超时: {cmd}")
                except Exception as e:
                    print(f"  ❌ 修复过程出错: {e}")
                    results.append(f"❌ 出错: {cmd} - {e}")
            
            if not auto_fix_attempted:
                print("  💡 请手动执行上述修复方案")
                results.append(f"💡 手动修复: {fix}")
            
            print()
        
        return "\\n".join(results) if results else "无修复结果"