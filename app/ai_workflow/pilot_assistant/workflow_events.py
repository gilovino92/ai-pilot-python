from typing import Any, Optional
from llama_index.core.llms import ChatMessage
from llama_index.core.tools import ToolSelection, ToolOutput
from llama_index.core.workflow import Event


class ModelInputEvent(Event):
    input: list[dict];
    max_recursion: int;
    
class ModelOutputEvent(Event):
    response: ChatMessage

class ModelResponseEvent(Event):
    model_response: Any
    conversation: list[dict]
    max_recursion: int

class ModelToolCallEvent(Event):
    message: Any
    conversation: list[dict]
    max_recursion: int

class ToolCallEvent(Event):
    tool_name: str
    tool_kwargs: Any

class ToolCallErrorEvent(Event):
    tool_name: str
    error: str
    
class ToolCallResultEvent(Event):
    tool_name: str
    result: Any

class StartStreamEvent(Event):
    pass

class StreamEvent(Event):
    content: str
    agent_action: Optional[str] = None
    type: Optional[str] = None

class StreamEndEvent(Event):
    content: str    
