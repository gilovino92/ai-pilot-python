from fastapi import APIRouter, HTTPException, Request, Depends
from sse_starlette.sse import EventSourceResponse
import logging
import asyncio
from llama_index.core.workflow import HumanResponseEvent
from app.tools.db import get_db
from app.models.pilotchat import PilotChat, PilotChatMessage
from app.api.deps import get_current_user
from starlette.background import BackgroundTask
from app.ai_workflow.workflow_factory import workflows
from app.ai_workflow.sale_agent_workflow import WorkflowSubscriber, SaleAgentWorkflow

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def get_chats(current_user: dict = Depends(get_current_user)):
    with get_db() as db:
        user_id = current_user.get("id")
        chats = (
            db.query(PilotChat)
            .filter(PilotChat.user_id == user_id)
            .order_by(PilotChat.created_at.desc())
            .limit(50)
            .all()
        )
        return {"data": chats}


@router.get("/{chat_id}")
async def get_chat(
    chat_id: str,
    page: int = 1,
    page_size: int = 100,
    current_user: dict = Depends(get_current_user),
):
    with get_db() as db:
        user_id = current_user.get("id")
        chat = (
            db.query(PilotChat)
            .filter(PilotChat.id == chat_id, PilotChat.user_id == user_id)
            .first()
        )
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        # Calculate offset
        offset = (page - 1) * page_size

        # Get total count
        total_messages = (
            db.query(PilotChatMessage).filter(PilotChatMessage.chat_id == chat_id).count()
        )

        # Get paginated messages
        messages = (
            db.query(PilotChatMessage)
            .filter(PilotChatMessage.chat_id == chat_id)
            .order_by(PilotChatMessage.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return {
            "data": messages,
            "pagination": {
                "total": total_messages,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_messages + page_size - 1) // page_size,
            },
        }


@router.post("")
async def create_chat(current_user: dict = Depends(get_current_user)):
    with get_db() as db:
        user_id = current_user.get("id")
        chat = PilotChat(user_id=user_id, context=None, serialized_context=None)
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return {"data": chat}


@router.post("/{chat_id}/messages")
async def add_message(
    chat_id: str, body: dict, current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user.get("id")
        workflow = await workflows.get_agent_chat_workflow(chat_id, user_id)
        print(workflow)
        if body["type"] == "USER_RESPONSE":
              workflow.ctx.send_event(
                    HumanResponseEvent(
                        response=body["message"],
                        user_id=user_id,
                    )
                )
        else:
            asyncio.create_task(workflow.run(input=body["message"]))

        message = {
            "chat_id": chat_id,
            "message": body["message"],
            "is_processed": False,
            }
        return message
    except Exception as e:
        logger.error(f"Error in add_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


SSE_HEADERS = {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",

}
async def event_generator(subscriber: WorkflowSubscriber, workflow: SaleAgentWorkflow, request: Request):
    try:
        # Send initial connection message
        yield {"event": "connected", "data": "Connected to the server"}
        while True:
            if await request.is_disconnected():
                print(f"Client disconnected (detected by request.is_disconnected)")
                break
            try:
                message = await asyncio.wait_for(subscriber.get_message(), timeout=10.0)
                if(message):
                    await asyncio.sleep(0.1)
                    yield {"event": "message", "data": message}
            except asyncio.TimeoutError:
                pass
        
    except asyncio.CancelledError:
        print(f"Client  disconnected (CancelledError)")
        raise
    except Exception as e:
        logger.error(f"Error in event_generator for client {subscriber.id}: {e}")

@router.get("/{chat_id}/stream")
async def stream(
    chat_id: str, request: Request, current_user: dict = Depends(get_current_user)
):
    with get_db() as db:
        user_id = current_user.get("id")
        chat = (
            db.query(PilotChat)
            .filter(PilotChat.id == chat_id, PilotChat.user_id == user_id)
            .first()
        )
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        workflow = await workflows.get_agent_chat_workflow(chat_id, user_id)
        subscriber = workflow.new_subscriber();
        print(f"there are {len(workflow.subscribers)} subscribers connected")


        return EventSourceResponse(
            event_generator(subscriber, workflow, request),
            headers=SSE_HEADERS,
            media_type="text/event-stream",
            background=BackgroundTask(workflows.cleanup,workflow = workflow, subscriber_id = subscriber.id)
        )