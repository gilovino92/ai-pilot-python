from llama_index.core.workflow import Context
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage
from llama_index.core.workflow import Context
# from app.ai_workflow.bedrock_workflow import ToolUseDemo
from app.tools.db import get_db
from app.models.pilotchat import PilotChatMessage
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.agent.workflow import (
    AgentWorkflow,
    AgentOutput,
    AgentOutput,
    ToolCall,
    ToolCallResult,
)
import json
import uuid
from app.ai_workflow.events import ToolCallStreamEvent, StartStreamEvent, StreamEndEvent
from llama_index.core.workflow import InputRequiredEvent
import asyncio
from typing import Optional
from app.ai_workflow.events import UserInputResponse
from app.models.pilotchat import PilotChat
from app.tools.console_tool import (
    print_info,
    print_warning,
    print_success,
    print_error,
    print_yellow_bg,
)
from app.ai_workflow.agents import get_company_agent
from llama_index.core.agent.workflow import FunctionAgent
from app.ai_workflow.LLMs import llm
from llama_index.tools.tavily_research.base import TavilyToolSpec
from app.config import settings

SALE_AGENT_NAME = "sale_agent"

SALE_AGENT_SYSTEM_PROMPT = """
You are X-Pilot Assistant, an AI specifically designed to support agricultural trading sales representatives. Your goal is to provide accurate, practical, and actionable information that helps agricultural sales professionals succeed in their daily work. You have deep expertise in agricultural commodities, international trade logistics, market analysis, sales communication, and relationship management within the agricultural sector.

Core Capabilities and Approach
Customer & Market Research
Provide detailed company verification guidance including how to check import/export history, certifications, and company reliability markers
Deliver current market insights on agricultural commodities with price trends, seasonal factors, and regional variations
Analyze market conditions affecting specific products (cashews, rice, pepper, etc.) with evidence-based insights
Format market data in clear, actionable tables and bullet points when appropriate

Sales Communication Support
Improve communication by enhancing message tone, clarity, and professionalism
Assist with translation and cultural nuances in international agricultural trade
Draft customized product offers, quotations, and proposals using industry-standard terminology
Structure communications to highlight key value propositions relevant to specific agricultural products
Include both formal and relationship-building elements appropriate to the sales context
Product & Logistics Knowledge
Explain documentation requirements for agricultural exports to specific markets
Provide clear guidance on phytosanitary certificates, quality certifications, and customs documentation
Simplify complex trade terms (INCOTERMS) using practical examples relevant to agricultural trade
Offer product-specific shipping and logistics recommendations with consideration for perishability, temperature control, and preservation
Deal Closing Support
Articulate key selling points for agricultural products with emphasis on origin, quality metrics, certifications, and competitive advantages
Prepare persuasive responses to common buyer objections regarding price, delivery time, and quality assurance
Suggest effective negotiation techniques specific to agricultural commodity trading
Identify red flags in potential deals and offer risk mitigation strategies
Performance & Strategy
Summarize and structure sales conversations into actionable insights for CRM entry
Recommend follow-up strategies based on conversation content and buyer signals
Share best practices for agricultural trade negotiations with cultural considerations
Provide templates for tracking sales performance specific to agricultural commodities
Response Style and Format
Always cite sources: Clearly indicate the origin of information with links to the sources
Be transparent about confidence levels: Distinguish between verified facts, industry standards, and professional judgments
Include reference links: When providing market data or regulatory information, always include links to official sources 
Be concise yet thorough: Sales representatives are busy; provide actionable information efficiently
Use industry terminology: Demonstrate familiarity with agricultural trade language while remaining accessible
Provide visual organization: Use formatting (tables, bullet points) to make information easy to scan and apply
Include practical examples: Connect advice to real-world agricultural trading scenarios
Maintain a professional, supportive tone: Be a knowledgeable colleague rather than a generic assistant
Structure responses logically: Present information in order of importance to the sales process
Balance detail with actionability: Provide enough information to be useful without overwhelming
Consider timing in the sales cycle: Tailor advice based on whether the rep is prospecting, negotiating, or closing
Specialized Knowledge Areas
Deep understanding of agricultural commodities and their quality parameters
Familiarity with international agricultural trade regulations and documentation
Knowledge of price factors and seasonal variations in agricultural markets
Awareness of supply chain considerations for perishable goods
Understanding of common certification standards in agricultural trade (Organic, Fair Trade, GlobalGAP, etc.)
Familiarity with cultural considerations in international agricultural business
Knowledge of typical payment terms and financial instruments in agricultural trade
When responding to queries, draw on this specialized knowledge while maintaining a practical focus on helping the sales representative succeed in their immediate task and long-term relationship building with agricultural buyers and suppliers.
Response Examples
When asked about market prices: "The current market price for Vietnamese cashew kernels (W320) is $3.20-3.40/kg FOB Ho Chi Minh City, showing a 5% increase since last month due to limited supply from early harvest. Key factors affecting this price include: [list factors]. Consider highlighting these market dynamics when discussing with your buyer to justify your pricing structure."
When asked about documentation: "To export organic rice from Thailand to Germany, you'll need: 1) Commercial Invoice, 2) Packing List, 3) Certificate of Origin, 4) Phytosanitary Certificate, 5) Organic Certification recognized by EU, 6) EUR.1 Movement Certificate to benefit from preferential duties, and 7) Bill of Lading. The most frequent delay occurs with the phytosanitary certificate, which requires inspection at least 7 days before shipment - plan accordingly to avoid postponing your vessel booking."
When asked about responding to a buyer: "Based on this buyer's message expressing concerns about moisture content in the coffee beans, I suggest this response structure:
Acknowledge their quality concerns directly
Explain your quality control process specifically for moisture (include exact measurement methods)
Offer documentation proof (moisture meter readings, lab results)
Propose a solution (replacement, discount, or third-party verification)
Reinforce relationship value Here's a draft response incorporating these elements: [draft message]"

Tool usage: tavily_search
Maximum search time: 3

Always remember that your purpose is to help agricultural sales representatives build successful, sustainable trading relationships while meeting their immediate business needs.
"""


SALE_AGENT_LLM = llm(system_prompt=SALE_AGENT_SYSTEM_PROMPT)

tavily_tool = TavilyToolSpec(
    api_key=settings.TAVILY_API_KEY,
)
def create_sale_agent(can_handoff_to: list[str]):
    sale_agent = FunctionAgent(
        name=SALE_AGENT_NAME,
        description=SALE_AGENT_SYSTEM_PROMPT,
        system_prompt=SALE_AGENT_SYSTEM_PROMPT,
        llm=SALE_AGENT_LLM,
        can_handoff_to=can_handoff_to,
        tools=tavily_tool.to_tool_list(),
    )
    return sale_agent


class WorkflowSubscriber:
    id: str
    message_queue: asyncio.Queue

    def __init__(self, id: str):
        self.id = id
        self.message_queue = asyncio.Queue()

    async def get_message(self):
        return await self.message_queue.get()

    async def put_message(self, message: str):
        await self.message_queue.put(message)


class SaleAgentWorkflow:
    id: str
    chat_id: str
    user_id: str
    messages: list[PilotChatMessage]
    memory: ChatMemoryBuffer
    root_agent: FunctionAgent
    agents: list[FunctionAgent]
    workflow: AgentWorkflow
    subscribers: list[WorkflowSubscriber]
    current_reply_message_id: str
    workflow_state: dict = {
        "language": "English",
    }

    def create_multi_agents(self):
        # TODO: ENABLE COMPANY AGENT LATER
        # company_agent = get_company_agent()
        # sale_agent = create_sale_agent([company_agent.name])
        # self.agents = [sale_agent, company_agent]

        sale_agent = create_sale_agent([])
        self.agents = [sale_agent]
        self.root_agent = sale_agent

    def prepare_workflow_memory(self):
        self.memory = ChatMemoryBuffer.from_defaults(
            llm=self.root_agent.llm, token_limit=1000
        )

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
                self.memory.put(ChatMessage(role=message.role, content=message.content))

    def __init__(self, id: str, chat_id: str, user_id: str) -> None:
        super().__init__()
        self.id = id
        self.subscribers = []
        self.chat_id = chat_id
        self.user_id = user_id
        self.messages = []

        self.create_multi_agents()

        self.workflow = AgentWorkflow(
            root_agent=self.root_agent.name,
            agents=self.agents,
            initial_state=self.workflow_state,
        )
        self.prepare_workflow_memory()

        self.ctx = Context(workflow=self.workflow)

    # TODO: add summary
    # async def get_summary(self):
    #     with get_db() as db:
    #         chat_history = []
    #         chat = (
    #             db.query(PilotChat)
    #             .filter(PilotChat.id == self.chat_id, PilotChat.user_id == self.user_id)
    #             .first()
    #         )
    #         context = chat.context
    #         if not context:
    #             self.messages = (
    #                 db.query(PilotChatMessage)
    #                 .filter(
    #                     PilotChatMessage.chat_id == self.chat_id,
    #                     PilotChatMessage.user_id == self.user_id,
    #                 )
    #                 .order_by(PilotChatMessage.created_at.desc())
    #                 .limit(50)
    #                 .all()
    #             )
    #             if len(self.messages) > 0:
    #                 for message in self.messages:
    #                     chat_history.append(
    #                         ChatMessage(role=message.role, content=message.content)
    #                     )
    #                 summary = ChatSummaryMemoryBuffer.from_defaults(
    #                     chat_history=chat_history,
    #                     llm=summarizer_llm(),
    #                     token_limit=256,
    #                     tokenizer_fn=tiktoken.encoding_for_model("gpt-4o-mini").encode,
    #                 )
    #                 chat_summary = summary.get()
    #                 print(f"Chat Summary: {chat_summary[0].content}")
    #             else:
    #                 print("No chat history found")

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
        self, content: str, role: str, type: str, id: Optional[str] = None
    ):
        message = json.dumps(
            {
                "id": id if id else "",
                "type": type,
                "content": content,
                "role": role,
                "chat_id": str(self.chat_id),
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
        self.memory.put(ChatMessage(role="user", content=input))

        # update context memory
        await self.ctx.set("memory", self.memory)

        # Get chat history and convert format
        chat_history = self.memory.get()
        formatted_history = []
        for msg in chat_history:
            formatted_history.append({
                "role": str(msg.role.value),
                "content": [{"text": str(msg.content)}]
            })
        # try: 
        #     bedrock_workflow = ToolUseDemo()
        #     response = bedrock_workflow.run(formatted_history, self.ctx, self.memory)
        #     print(response)
        # except Exception as e:
        #     print(e)
        # Run agent
        # try:
            # handler = self.workflow.run(
            #     user_msg=input, chat_history=chat_history, ctx=self.ctx, memory=self.memory
            # )

        #     # Stream events
        #     current_agent = None
        #     async for event in handler.stream_events():
        #         try:
        #             if (
        #                 hasattr(event, "current_agent_name")
        #                 and event.current_agent_name != current_agent
        #             ):
        #                 current_agent = event.current_agent_name
        #                 print(f"\n{'='*50}")
        #                 print(f"🤖 Agent: {current_agent}")
        #                 print(f"{'='*50}\n")

        #             elif isinstance(event, StartStreamEvent):
        #                 message = self.store_message(
        #                     "", "assistant", self.chat_id, "START_STREAM"
        #                 )
        #                 self.current_reply_message_id = message.id
        #                 self.publish_message(
        #                     "", "assistant", "START_STREAM", str(self.current_reply_message_id)
        #                 )
        #                 print_success(
        #                     f"START STREAMING... - chat_id: {self.chat_id}, user_id: {self.user_id}"
        #                 )
        #             elif isinstance(event, StreamEndEvent):
        #                 self.update_message(
        #                     self.current_reply_message_id,
        #                     {
        #                         "content": event.content,
        #                         "role": "assistant", 
        #                         "type": "AGENT_RESPONSE",
        #                         "chat_id": self.chat_id,
        #                     },
        #                 )
        #                 self.publish_message("", "assistant", "ALLOW_USER_INPUT")
        #                 print_error(
        #                     f"STREAMING ENDED - chat_id: {self.chat_id}, user_id: {self.user_id}"
        #                 )

        #             elif isinstance(event, ToolCallStreamEvent):
        #                 print_error(
        #                     f"Calling Stream tool: {event.tool_name} with data: {event.data}"
        #                 )
        #                 self.publish_message(
        #                     event.data,
        #                     "assistant",
        #                     "STREAM", 
        #                     str(self.current_reply_message_id),
        #                 )

        #             elif isinstance(event, InputRequiredEvent):
        #                 print_warning(
        #                     f"Human in the loop - await for user input: {event.prefix}"
        #                 )
        #                 self.store_and_publish_message(
        #                     event.prefix, "assistant", "INPUT_REQUIRED"
        #                 )
        #                 self.publish_message("", "assistant", "ALLOW_USER_INPUT")

        #             elif isinstance(event, UserInputResponse):
        #                 print_info(f"Human response: {event.response}")
        #                 self.store_and_publish_message(event.response, "user", "USER_RESPONSE")

        #             elif isinstance(event, AgentOutput):
        #                 if event.response.content:
        #                     print_warning(
        #                         f"Agent response:\n**{event.response.model_dump_json()}**"
        #                     )
        #                     self.store_and_publish_message(
        #                         event.response.content, "assistant", "AGENT_RESPONSE"
        #                     )
        #                     self.publish_message("", "assistant", "ALLOW_USER_INPUT")
        #                 if event.tool_calls:
        #                     print_yellow_bg(
        #                         f"Agent planning to use tools: {[call.tool_name for call in event.tool_calls]}"
        #                     )

        #             elif isinstance(event, ToolCall):
        #                 print_error(
        #                     f"Calling Tool:\n_tool_name: {event.tool_name}\n_tool_kwargs: {event.tool_kwargs}"
        #                 )

        #             elif isinstance(event, ToolCallResult):
        #                 print_success(
        #                     f"Tool called done:\n_tool_name: {event.tool_name}\n_tool_kwargs: {event.tool_kwargs}\n_tool_output: {event.tool_output}\n_return_direct: {event.return_direct}"
        #                 )

        #         except Exception as e:
        #             print(f"Error processing event: {str(e)}")
        #             self.store_and_publish_message(
        #                 f"An error occurred while processing the response: {str(e)}", 
        #                 "assistant",
        #                 "ERROR"
        #             )
        #             self.publish_message("", "assistant", "ALLOW_USER_INPUT")

        # except Exception as e:
        #     print(f"Error running workflow: {str(e)}")
        #     self.store_and_publish_message(
        #         f"An error occurred while processing your request: {str(e)}", 
        #         "assistant",
        #         "ERROR"
        #     )
        #     self.publish_message("", "assistant", "ALLOW_USER_INPUT")
