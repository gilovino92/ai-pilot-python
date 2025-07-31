import uuid
from app.tools.console_tool import print_warning, print_yellow_bg, print_red_bg
from app.ai_workflow.pilot_assistant.agent import PilotAssistant
from llama_index.core.workflow import HumanResponseEvent

class WorkflowFactory:
    agent_chat_workflows: list[PilotAssistant] = []

    def __init__(self):
        pass

    def init_agent_chat_workflow(self, chat_id: str, user_id: str):
        id = str(uuid.uuid4())
        workflow = PilotAssistant(id, chat_id, user_id)
        print_warning(f"Initialized workflow {id} with chat_id: {chat_id} and user_id: {user_id}")
        self.agent_chat_workflows.append(workflow)
        return workflow

    async def get_agent_chat_workflow(self, chat_id: str, user_id: str):
        for workflow in self.agent_chat_workflows:
            if workflow.chat_id == chat_id and workflow.user_id == user_id:
                return workflow
        workflow = self.init_agent_chat_workflow(chat_id, user_id)
        await workflow.ctx.set("is_waiting_for_customer_response", False)
        return workflow
    
    async def cleanup(self, workflow: PilotAssistant, subscriber_id: str):
        # Remove current subscriber from workflow
        found = next((i for i, subscriber in enumerate(workflow.subscribers) if subscriber.id == subscriber_id), None)
        if(found is not None):
            workflow.subscribers.pop(found)
            print_yellow_bg(f"Subscriber {subscriber_id} of chat {workflow.chat_id}, user {workflow.user_id} cleaned up via background task")

        # Abort human response wait if waiting for customer response
        async def abort_human_response_wait(workflow: PilotAssistant):
            is_waiting_for_customer_response = await workflow.ctx.get("is_waiting_for_customer_response")
            if(is_waiting_for_customer_response):
                workflow.ctx.send_event(
                    HumanResponseEvent(
                    response='aborted',
                    user_id=workflow.user_id,
                    )
                )
                await workflow.ctx.set("is_waiting_for_customer_response", False)
            if(len(workflow.subscribers) == 0):
                self.shutdown(workflow.id)
        await abort_human_response_wait(workflow)

    def shutdown(self, id: str):
        for workflow in self.agent_chat_workflows:
            if workflow.id == id:
                self.agent_chat_workflows.remove(workflow)
                print_red_bg(f"Workflow with id {id}, chat_id {workflow.chat_id}, user_id {workflow.user_id} shutdown")
                return


workflows = WorkflowFactory()

__all__ = [workflows]