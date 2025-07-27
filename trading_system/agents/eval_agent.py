from typing import List, Any, Optional, Dict, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from typing import Annotated

DEFAULT_SUCCESS_CRITERIA = "Generate a clear, accurate, and tool-supported market insight that answers the user’s request without making unsupported claims."

class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool

class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the work done by the agent")
    success_criteria_met: bool = Field(description="Whether the success criteria was met")
    user_input_needed: bool = Field(description="Whether the user needs to provide input")

class EvaluatorAgent:
    def __init__(self, structured_llm=None):
        self.evaluator_llm_with_output = structured_llm

    async def setup(self):
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)

    def _ensure_success_criteria(self, state: State) -> State:
        if not state.get("success_criteria"):
            state["success_criteria"] = DEFAULT_SUCCESS_CRITERIA
        return state

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = "Conversation history:\n\n"
        for message in messages:
            sender = "Unknown"
            if hasattr(message, "metadata") and "sender" in message.metadata:
                sender = message.metadata["sender"]
            elif isinstance(message, HumanMessage):
                sender = "User"
            elif isinstance(message, AIMessage):
                sender = "Assistant"

            if isinstance(message, AIMessage):
                text = message.content or "[Tool use / No content]"
            else:
                text = message.content

            conversation += f"{sender}: {text}\n"
        return conversation

    def evaluate(self, state: State) -> State:
        state = self._ensure_success_criteria(state)
        last_response = state["messages"][-1].content

        system_message = """You are an evaluator assessing whether a market intelligence analyst has successfully completed a task. Your job is to determine whether the final response meets the user's success criteria and whether further user input is needed."""

        user_message = f"""You are evaluating a conversation between the User and the Market Intelligence Analyst.

### Conversation History
{self.format_conversation(state['messages'])}

### Success Criteria
{state['success_criteria']}

### Final Response from Analyst
{last_response}

Evaluate whether the final response meets the success criteria. If it does not, provide specific feedback.

Also, determine whether the analyst requires further input from the user (e.g., clarification, missing context, or the analyst appears stuck).

The analyst has access to data and web tools. You can assume any stated research was performed. However, reject answers that seem incomplete or superficial.

Respond with:
- Constructive feedback on the analyst's final answer
- Whether the success criteria has been met
- Whether the analyst requires further user input
"""

        if state["feedback_on_work"]:
            user_message += f"Also, note that in a prior attempt from the Analyst, you provided this feedback: {state['feedback_on_work']}\n"
            user_message += "If you're seeing the Analyst repeating the same mistakes, then consider responding that user input is required."

        evaluator_messages = [SystemMessage(content=system_message), HumanMessage(content=user_message)]

        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)

        new_state = {
            "messages": [
                AIMessage(
                    content=f"Evaluator Feedback on this answer: {eval_result.feedback}",
                    metadata={"sender": "evaluator"}
                )
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed
        }
        return new_state
    
def build_market_intel_evaluator(eval_llm) -> Tuple:
    structured_llm = eval_llm.with_structured_output(EvaluatorOutput)
    agent = EvaluatorAgent(structured_llm)
    return structured_llm, agent

def build_technical_analyst_evaluator(eval_llm) -> Tuple:
    structured_llm = eval_llm.with_structured_output(EvaluatorOutput)
    agent = EvaluatorAgent(structured_llm)
    return structured_llm, agent