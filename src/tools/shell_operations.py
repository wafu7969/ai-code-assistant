"""
Shell 执行工具模块

提供跨平台的命令执行功能，包括实时输出捕获、错误检测和超时控制。
"""
import subprocess
import threading
import queue
from typing import Optional, Tuple

class ShellExecutor:
    """Shell 执行工具类"""

    def __init__(self, timeout: Optional[int] = None):
        """
        初始化 Shell 执行工具

        Args:
            timeout: 命令执行的超时时间（秒）
        """
        self.timeout = timeout or 10  # 默认10秒超时

    def execute(self, command: str, cwd: Optional[str] = None) -> Tuple[int, str, str]:
        """
        执行 Shell 命令

        Args:
            command: 要执行的命令字符串
            cwd: 命令执行的工作目录

        Returns:
            一个元组 (返回码, 标准输出, 标准错误)
        """
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(timeout=self.timeout)
            return process.returncode, stdout, stderr

        except subprocess.TimeoutExpired:
            process.kill()
            return -1, "", "命令执行超时"

        except Exception as e:
            return -1, "", str(e)

    def execute_with_realtime_output(self, command: str, cwd: Optional[str] = None) -> int:
        """
        执行 Shell 命令并实时输出日志

        Args:
            command: 要执行的命令字符串
            cwd: 命令执行的工作目录

        Returns:
            返回码
        """
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            def log_stream(stream):
                for line in iter(stream.readline, ""):
                    print(line, end="")

            stdout_thread = threading.Thread(target=log_stream, args=(process.stdout,))
            stderr_thread = threading.Thread(target=log_stream, args=(process.stderr,))

            stdout_thread.start()
            stderr_thread.start()

            stdout_thread.join()
            stderr_thread.join()

            return process.wait()

        except Exception as e:
            print(f"执行命令时发生错误: {e}")
            return -1

    def start_server(self, command: str, cwd: Optional[str] = None, check_timeout: int = 5) -> Tuple[bool, subprocess.Popen, str]:
        """
        启动服务器进程（非阻塞）并检测启动错误

        Args:
            command: 要执行的命令字符串
            cwd: 命令执行的工作目录
            check_timeout: 检查服务器启动的超时时间（秒）

        Returns:
            一个元组 (启动成功, 进程对象, 消息)
        """
        try:
            # 首先进行预检查 - 对于包含&&的命令，先执行第一部分
            if " && " in command:
                parts = command.split(" && ", 1)
                first_command = parts[0].strip()
                
                # 执行第一部分命令（如 npm install）
                print(f"🔍 预执行命令: {first_command}")
                first_result = self.execute(first_command, cwd)
                
                if first_result[0] != 0:
                    # 第一部分失败，直接返回错误
                    return False, None, f"预执行命令失败: {first_result[2] or first_result[1]}"
                
                # 第一部分成功，执行第二部分
                command = parts[1].strip()
                print(f"✅ 预执行成功，开始启动服务: {command}")
            
            # 启动服务进程
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            import time
            
            # 用于收集输出的队列
            output_queue = queue.Queue()
            error_queue = queue.Queue()
            
            def read_output(pipe, q):
                try:
                    for line in iter(pipe.readline, ''):
                        q.put(line)
                except:
                    pass
            
            # 启动输出读取线程
            stdout_thread = threading.Thread(target=read_output, args=(process.stdout, output_queue))
            stderr_thread = threading.Thread(target=read_output, args=(process.stderr, error_queue))
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()
            
            # 收集启动期间的输出
            startup_output = []
            startup_errors = []
            
            # 等待并检查启动期间的输出
            for i in range(check_timeout):
                time.sleep(1)
                
                # 检查进程是否已退出
                if process.poll() is not None:
                    # 收集剩余输出
                    try:
                        while True:
                            startup_output.append(output_queue.get_nowait())
                    except queue.Empty:
                        pass
                    try:
                        while True:
                            startup_errors.append(error_queue.get_nowait())
                    except queue.Empty:
                        pass
                    
                    combined_output = ''.join(startup_output + startup_errors)
                    return False, None, f"服务器启动失败: {combined_output}"
                
                # 收集可用的输出
                try:
                    while True:
                        startup_output.append(output_queue.get_nowait())
                except queue.Empty:
                    pass
                
                try:
                    while True:
                        startup_errors.append(error_queue.get_nowait())
                except queue.Empty:
                    pass
            
            # 分析输出中的错误指示
            combined_output = ''.join(startup_output + startup_errors).lower()
            
            error_indicators = [
                "error", "错误", "failed", "失败", 
                "cannot", "不能", "unable", "无法",
                "missing", "缺失", "not found", "未找到",
                "语句分隔符", "parsererror", "unexpected token",
                "enoent", "command not found", "cannot find module"
            ]
            
            detected_errors = []
            for indicator in error_indicators:
                if indicator in combined_output:
                    detected_errors.append(indicator)
            
            if detected_errors:
                full_output = ''.join(startup_output + startup_errors)
                return False, process, f"服务器启动检测到错误 ({', '.join(detected_errors)}): {full_output}"
            
            # 检查进程是否仍在运行
            if process.poll() is None:
                return True, process, f"服务器启动成功，PID: {process.pid}"
            else:
                # 进程已退出，获取错误信息
                full_output = ''.join(startup_output + startup_errors)
                return False, None, f"服务器进程已退出: {full_output}"
                
        except Exception as e:
            return False, None, f"启动服务器时发生错误: {e}"