"""
使用create_react_agent实现，智能判断是否需要读取项目文件
"""
from typing import Optional
from ..models.llm_provider import LLMProvider
from ..tools.file_operations import build_file_tools


class QuestionHandler:
    """简化的问题解答处理器"""
    
    def __init__(self, 
                 llm_provider: Optional[LLMProvider] = None,
                 root: Optional[str] = None, 
                 output_dir: str = "output"):
        """
        初始化问题解答处理器
        
        Args:
            llm_provider: LLM提供者
            root: 项目根目录
            output_dir: 输出目录
        """
        self.llm_provider = llm_provider or LLMProvider()
        self.root = root
        self.output_dir = output_dir
    
    def handle_question(self, question: str) -> str:
        """
        处理用户问题
        
        Args:
            question: 用户问题
            
        Returns:
            回答内容
        """
        try:
            print("🤖 正在使用ReAct Agent分析并回答问题...")
            
            # 加载模型
            model = self.llm_provider.load_model()
            if model is None:
                return "抱歉，AI模型未正确加载，无法回答您的问题。"
            
            # 构建文件操作工具
            file_tools = build_file_tools(self.root, self.output_dir)
            
            if not file_tools:
                print("⚠️ 文件工具加载失败，使用通用回答模式")
                return self._handle_general_question(question)
            
            # 使用ReAct Agent
            return self._use_react_agent(question, model, file_tools)
            
        except Exception as e:
            print(f"❌ 处理问题时出错: {e}")
            return f"抱歉，处理您的问题时出现错误：{str(e)}"
    
    def _use_react_agent(self, question: str, model, tools: list) -> str:
        """
        使用ReAct Agent处理问题
        
        Args:
            question: 用户问题
            model: LLM模型
            tools: 工具列表
            
        Returns:
            回答内容
        """
        try:
            from langchain.agents import create_react_agent, AgentExecutor
            from langchain_core.prompts import PromptTemplate
            
            # 创建智能问答提示模板 - 使用标准ReAct格式
            prompt = PromptTemplate.from_template("""
                Answer the following questions as best you can. You have access to the following tools:

                {tools}

                Use the following format:

                Question: the input question you must answer
                Thought: you should always think about what to do
                Action: the action to take, should be one of [{tool_names}]
                Action Input: the input to the action
                Observation: the result of the action
                ... (this Thought/Action/Action Input/Observation can repeat N times)
                Thought: I now know the final answer
                Final Answer: the final answer to the original input question

                Begin!

                Question: {input}
                Thought: 我需要分析用户问题的类型。如果涉及项目相关内容，我需要查看项目文件；如果是通用编程问题，我可以直接回答。
                {agent_scratchpad}
            """)
            
            # 错误计数器
            format_error_count = 0
            max_format_errors = 2  # 问答模式允许的错误次数较少
            
            # 自定义解析错误处理函数
            def custom_parsing_error_handler(error_message) -> str:
                """自定义解析错误处理，避免无限循环"""
                nonlocal format_error_count
                format_error_count += 1
                
                # 确保 error_message 是字符串格式
                error_str = str(error_message)
                print(f"🚨 第{format_error_count}次解析错误: {error_str}")
                
                if format_error_count >= max_format_errors:
                    print(f"⚠️ 解析错误次数达到上限({max_format_errors})，切换到通用回答模式")
                    raise Exception(f"解析错误次数过多，切换到备用模式")
                
                if "Invalid Format" in error_str and "Missing 'Action:' after 'Thought:'" in error_str:
                    print("⚠️ 检测到ReAct格式错误，尝试修正...")
                    return "请使用正确的格式: Thought: 你的思考过程 Action: 选择一个工具 Action Input: 工具的输入"
                elif "Invalid Format" in error_str:
                    print(f"⚠️ 检测到格式错误，尝试修正...")
                    return "请遵循标准的ReAct格式: Thought -> Action -> Action Input -> Observation"
                
                return f"解析错误: {error_str}"
            
            # 创建ReAct Agent
            agent = create_react_agent(model, tools, prompt)
            
            # 创建Agent执行器
            agent_executor = AgentExecutor(
                agent=agent, 
                tools=tools, 
                verbose=False,  # 是否开启详细输出以便调试
                max_iterations=150,  # 减少迭代次数避免超时
                max_execution_time=3000,  # 30秒超时
                handle_parsing_errors=custom_parsing_error_handler,
                return_intermediate_steps=False
            )
            
            # 执行查询
            result = agent_executor.invoke({"input": question})
            
            return result.get("output", "抱歉，未能生成完整的回答。")
            
        except Exception as e:
            print(f"⚠️ ReAct Agent执行失败: {e}")
            return self._handle_general_question(question)
    
    def _handle_general_question(self, question: str) -> str:
        """
        处理通用问题（作为降级方案）
        
        Args:
            question: 用户问题
            
        Returns:
            回答内容
        """
        try:
            model = self.llm_provider.load_model()
            if model is None:
                return "抱歉，AI模型未正确加载，无法回答您的问题。"
            
            from langchain_core.messages import HumanMessage
            
            prompt = f"""
你是一个专业的编程助手。请回答用户的问题，提供准确、详细且实用的信息。

用户问题: {question}

请提供：
1. 直接回答问题
2. 相关的技术要点
3. 最佳实践建议
4. 如果适用，提供简单的示例代码

回答应该清晰、专业且易于理解。
"""
            
            response = model.invoke([HumanMessage(content=prompt)])
            return response.content
            
        except Exception as e:
            return f"抱歉，无法回答您的问题。错误信息：{str(e)}"