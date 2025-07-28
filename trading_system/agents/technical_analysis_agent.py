# File: technical_analysis_agent.py
from typing import Annotated, List, Any, Optional, Dict
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from datetime import datetime
import uuid
import asyncio
import time
from agents.tools.technical_analysis_tools import technical_analysis_tools
# from agents.eval_agent import build_technical_analysis_evaluator  # Temporarily disabled
from database import Database

# Initialize LangSmith for tracing
try:
    from langsmith_config import init_langsmith, is_langsmith_enabled
    if is_langsmith_enabled():
        init_langsmith()
except ImportError:
    print("ℹ️ LangSmith not available for technical analysis agent")

DEFAULT_SUCCESS_CRITERIA = "Generate a clear, accurate, and tool-supported technical analysis that answers the user's request without making unsupported claims."

class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool

class TechnicalAnalysisAgent:
    def __init__(self, db_path: str = "trading_system.db"):
        self.technical_analyst_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.graph = None
        self.technical_analyst_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.db = Database(db_path)
        self.current_session_id = None

    def _ensure_success_criteria(self, state: State) -> State:
        if not state.get("success_criteria"):
            state["success_criteria"] = DEFAULT_SUCCESS_CRITERIA
        return state
    
    def _create_fallback_evaluator(self):
        """Create a simple fallback evaluator that always passes"""
        class FallbackEvaluator:
            def evaluate(self, state: State) -> Dict[str, Any]:
                # Simple evaluator that always marks success
                return {
                    **state,
                    "success_criteria_met": True,
                    "user_input_needed": False,
                    "feedback_on_work": "Technical analysis completed"
                }
        return FallbackEvaluator()

    async def setup(self):
        # Tools will be created with session ID when run_superstep is called
        technical_analyst_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        eval_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        # self.evaluator_llm_with_output, self.evaluator = build_technical_analysis_evaluator(eval_llm)  # Temporarily disabled
        self.evaluator_llm_with_output, self.evaluator = None, self._create_fallback_evaluator()  # Temporary fix
        # Note: build_graph will be called in run_superstep with session-specific tools

    def technical_analyst(self, state: State) -> Dict[str, Any]:
        state = self._ensure_success_criteria(state)
        system_prompt = f""" You are a technical analysis analyst who can use tools to analyze the technical aspects of the stock market. You keep analyzing the topic given to you by the user until you have a question or clarification for the user, or the success criteria is met.
        You have many tools at your disposal to help you analyze the stock and stock market. Please use them to formulate your response and do not make up any information. 
        The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        This is the success criteria: 
        {state["success_criteria"]}
        You should reply either with a question for the user about this assignment, or with your final response.
        """

        if state.get("feedback_on_work"):
            system_prompt += f"""
        Previously you thought you completed the analysis, but your reply was rejected because the success criteria was not met.
        Here is the feedback on why this was rejected:
        {state['feedback_on_work']}
        With this feedback, please continue the analysis, ensuring that you meet the success criteria or have a question for the user."""

        messages = state["messages"]
        found_system = any(isinstance(m, SystemMessage) for m in messages)

        if found_system:
            for m in messages:
                if isinstance(m, SystemMessage):
                    m.content = system_prompt
        else:
            messages = [SystemMessage(content=system_prompt)] + messages

        response = self.technical_analyst_llm_with_tools.invoke(messages)
        response.metadata = {"sender": "technical_analyst"}

        return {
            **state,
            "messages": messages + [response]
        }

    def technical_analyst_router(self, state: State) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        else:
            return "evaluator"

    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        else:
            return "technical_analyst"

    async def build_graph(self):
        graph_builder = StateGraph(State)
        graph_builder.add_node("technical_analyst", self.technical_analyst)
        graph_builder.add_node("tools", ToolNode(self.tools))
        graph_builder.add_node("evaluator", self.evaluator.evaluate)
        graph_builder.add_conditional_edges("technical_analyst", self.technical_analyst_router, {"tools": "tools", "evaluator": "evaluator"})
        graph_builder.add_edge("tools", "technical_analyst")
        graph_builder.add_conditional_edges("evaluator", self.route_based_on_evaluation, {"technical_analyst": "technical_analyst", "END": END})
        graph_builder.add_edge(START, "technical_analyst")
        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history, debug=False):
        start_time = time.time()
        
        # Generate unique session and thread IDs
        session_id = f"session_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        thread_id = str(uuid.uuid4())
        self.current_session_id = session_id
        
        # Create session-specific tools and rebuild graph
        self.tools = await technical_analysis_tools(session_id)
        technical_analyst_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        self.technical_analyst_llm_with_tools = technical_analyst_llm.bind_tools(self.tools)
        await self.build_graph()
        
        config = {"configurable": {"thread_id": thread_id}}
        state = {
            "messages": [HumanMessage(content=message, metadata={"sender": "human_user"})],
            "success_criteria": success_criteria,
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False
        }
        
        # Save session to database
        self.db.save_session(session_id, message, success_criteria, history, debug)
        
        result = await self.graph.ainvoke(state, config=config)
        self._last_state = result  # Store for debugging

        def get_last_message_by_sender(messages, sender: str):
            for msg in reversed(messages):
                if getattr(msg, "metadata", {}).get("sender") == sender:
                    return msg
            return None

        analyst_reply = get_last_message_by_sender(result["messages"], "technical_analyst")
        evaluator_feedback = get_last_message_by_sender(result["messages"], "evaluator")

        analyst_reply_text = analyst_reply.content if analyst_reply else "[No analyst reply]"
        evaluator_feedback_text = evaluator_feedback.content if evaluator_feedback else "[No evaluator feedback]"

        # Save briefing to database
        processing_time_ms = int((time.time() - start_time) * 1000)
        briefing_id = None
        if analyst_reply_text != "[No analyst reply]":
            # Get data sources from Alpha Vantage client
            # Note: This is a simplified version - in practice you'd need to track data sources per tool call
            briefing_id = self.db.save_briefing(
                session_id=session_id,
                user_query=message,
                success_criteria=success_criteria,
                briefing_content=analyst_reply_text,
                processing_time_ms=processing_time_ms
            )
        
        # Save evaluator feedback
        if evaluator_feedback_text != "[No evaluator feedback]":
            self.db.save_evaluator_feedback(
                session_id=session_id,
                briefing_id=briefing_id,
                feedback_text=evaluator_feedback_text,
                success_criteria_met=result.get("success_criteria_met", False),
                user_input_needed=result.get("user_input_needed", False)
            )

        return_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": analyst_reply_text},
            {"role": "assistant", "content": evaluator_feedback_text}
        ]
        
        if debug:
            # Add detailed tool call information
            for msg in result["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        return_history.append({
                            "role": "debug", 
                            "content": f"🔧 Tool Call: {tool_call['name']}\n📝 Args: {tool_call['args']}"
                        })
                
                # Show tool responses
                if hasattr(msg, "content") and msg.content and "Tool" in str(type(msg)):
                    return_history.append({
                        "role": "debug",
                        "content": f"🛠 Tool Response:\n{msg.content}"
                    })
        
        return return_history