from llama_index.core.llms import ChatMessage
from llama_index.core.tools import ToolSelection, ToolOutput
from llama_index.core.workflow import Event


class InputEvent(Event):
    input: list[ChatMessage]

class StreamEvent(Event):
    delta: str

class ToolCallEvent(Event):
    tool_calls: list[ToolSelection]

class ToolCallStreamEvent(Event):
    tool_name: str
    tool_kwargs: dict
    tool_id: str
    data: str


class FunctionOutputEvent(Event):
    output: ToolOutput

class StartStreamEvent(Event):
    tool_name: str

class StreamEndEvent(Event):
    content: str
    tool_name: str

class UserInputResponse(Event):
    response: str
