from llama_index.core.workflow import Context
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage
from llama_index.core.workflow import Context
from app.tools.db import get_db
from app.models.pilotchat import PilotChatMessage
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.agent.workflow import (
    AgentWorkflow,
)
import json
import uuid
import asyncio
from typing import Optional
from app.models.pilotchat import PilotChat
from app.tools.console_tool import (
    print_info,
    print_warning,
    print_success,
    print_error,
    print_yellow_bg,
)
from app.ai_workflow.pilot_assistant.types import WorkflowSubscriber
from app.ai_workflow.pilot_assistant.workflow import PilotAssistantWorkflow
from llama_index.core.workflow import (
    Context,
    StopEvent,
)
from app.ai_workflow.pilot_assistant.workflow_events import (
    ToolCallEvent,
    ToolCallResultEvent,
    ToolCallErrorEvent,
    ModelToolCallEvent,
    ModelOutputEvent,
    StartStreamEvent,
    StreamEndEvent,
    StreamEvent,
)
import threading

class PilotAssistant:
    id: str
    chat_id: str
    user_id: str
    messages: list[PilotChatMessage]
    chat_history: list[ChatMessage]
    root_agent: FunctionAgent
    agents: list[FunctionAgent]
    workflow: AgentWorkflow
    subscribers: list[WorkflowSubscriber]
    current_reply_message_id: str
    workflow_state: dict = {
        "language": "English",
    }

    def prepare_workflow_memory(self):
        self.chat_history = [];

        with get_db() as db:
            chat = (
                db.query(PilotChat)
                .filter(PilotChat.id == self.chat_id, PilotChat.user_id == self.user_id)
                .first()
            )
            self.messages = (
                db.query(PilotChatMessage)
                .filter(
                    PilotChatMessage.chat_id == self.chat_id,
                    PilotChatMessage.user_id == self.user_id,
                )
                .order_by(PilotChatMessage.created_at.desc())
                .limit(50)
                .all()
            )
            if len(self.messages) > 0:
                first_user_message = next(
                    (msg for msg in self.messages if msg.role == "user"), None
                )
                if first_user_message:
                    chat.title = first_user_message.content[:50]
                    db.commit()
                    db.refresh(chat)
            for message in self.messages:
                self.chat_history.insert(0, ChatMessage(role=message.role, content=message.content))

    def __init__(self, id: str, chat_id: str, user_id: str) -> None:
        super().__init__()
        self.id = id
        self.subscribers = []
        self.chat_id = chat_id
        self.user_id = user_id
        self.messages = []

        self.prepare_workflow_memory()
        self.workflow = PilotAssistantWorkflow()

        self.ctx = Context(workflow=self.workflow)

    def new_subscriber(self):
        client_subscriber = WorkflowSubscriber(str(uuid.uuid4()))
        self.subscribers.append(client_subscriber)
        print_info(
            f"NEW_SUBSCRIBER_ADDED: Workflow with\n_chat_id:{self.chat_id}\n_user_id:{self.user_id}\n_subscriber_id:{client_subscriber.id}\n_total_subscribers:{len(self.subscribers)}"
        )
        return client_subscriber

    def store_message(self, content: str, role: str, chat_id: str, type: str):
        with get_db() as db:
            message = PilotChatMessage(
                content=content,
                role=role,
                chat_id=chat_id,
                user_id=self.user_id,
                type=type,
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            return message

    def update_message(self, id: str, dict: dict):
        with get_db() as db:
            message = db.query(PilotChatMessage).filter(PilotChatMessage.id == id).first()
            for key, value in dict.items():
                setattr(message, key, value)
            db.commit()
            db.refresh(message)
            return message

    def publish_message(
        self, content: str, role: str, type: str, id: Optional[str] = None, agent_action: Optional[str] = None
    ):
        message = json.dumps(
            {
                "id": id if id else "",
                "type": type,
                "content": content,
                "role": role,
                "chat_id": str(self.chat_id),
                "agent_action": agent_action,
            }
        )
        for subscriber in self.subscribers:
            asyncio.create_task(subscriber.put_message(message))

    def store_and_publish_message(self, content: str, role: str, type: str):
        message = self.store_message(content, role, self.chat_id, type)
        self.publish_message(content, role, type, str(message.id))
        if type != "ALLOW_USER_INPUT":
            print_success(f"[{type}] {self.chat_id}: {content}")
        return message


    async def run(self, input: str):
        # Receive and store user query
        self.store_and_publish_message(input, "user", "USER_QUERY")

        # Update context
        await self.ctx.set("user_id", self.user_id)
        await self.ctx.set("chat_id", self.chat_id)
        print_info(f"chat_history: {self.chat_history}")

        # update context memory
        self.chat_history.append(ChatMessage(role="user", content=input))
        await self.ctx.set("chat_history", self.chat_history)
        try:
            handler = self.workflow.run(ctx=self.ctx)
            async for event in handler.stream_events():
                if isinstance(event, ModelOutputEvent):
                    if event.response.content:
                        self.store_and_publish_message(
                            event.response.content, "assistant", "AGENT_RESPONSE"
                        )
                elif isinstance(event, StopEvent):
                    if(self.current_reply_message_id):
                        self.update_message(
                            self.current_reply_message_id,
                            {
                                "content": event.result.get("response"),
                                "role": "assistant", 
                                "type": "AGENT_RESPONSE",
                                "chat_id": self.chat_id,
                            },
                        )
                        self.chat_history.append(ChatMessage(role="assistant", content=event.result.get("response")))
                        await self.ctx.set("chat_history", self.chat_history)
                        self.current_reply_message_id = None
                    else:
                        self.store_and_publish_message(
                            event.result.get("response"), "assistant", "AGENT_RESPONSE"
                        )
                        self.chat_history.append(ChatMessage(role="assistant", content=event.result.get("response")))
                        await self.ctx.set("chat_history", self.chat_history)
                    self.publish_message("", "assistant", "ALLOW_USER_INPUT")

                elif isinstance(event, ModelToolCallEvent):
                    pass
                elif isinstance(event, ToolCallResultEvent):
                    pass
                elif isinstance(event, ToolCallErrorEvent):
                    pass
                elif isinstance(event, StartStreamEvent):
                    message = self.store_message(
                        "", "assistant", self.chat_id, "START_STREAM"
                    )
                    self.current_reply_message_id = message.id
                    self.publish_message(
                        "", "assistant", "START_STREAM", str(self.current_reply_message_id)
                    )
                # elif isinstance(event, StreamEndEvent):
                #     self.update_message(
                #         self.current_reply_message_id,
                #         {
                #             "content": event.content,
                #             "role": "assistant", 
                #             "type": "AGENT_RESPONSE",
                #             "chat_id": self.chat_id,
                #         },
                #     )
                #     self.publish_message("", "assistant", "ALLOW_USER_INPUT")

                elif isinstance(event, StreamEvent):
                    self.publish_message(
                        event.content,
                        "assistant",
                        "STREAM",
                        str(self.current_reply_message_id),
                        event.agent_action if event.agent_action else None
                    )
        except Exception as e:
                print(e)
           