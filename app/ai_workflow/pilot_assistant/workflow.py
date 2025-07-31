import asyncio
from typing import Any, List

from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.tools.types import BaseTool
from llama_index.core.llms import ChatMessage
from llama_index.core.workflow import (
    Context,
    Workflow,
    StartEvent,
    StopEvent,
    step,
)

from .workflow_events import (
    ModelInputEvent,
    ModelResponseEvent,
    ModelToolCallEvent,
    ToolCallEvent,
    ToolCallResultEvent,
    ToolCallErrorEvent,
    ModelOutputEvent,
    StartStreamEvent,
    StreamEvent,
    StreamEndEvent,
)
from enum import Enum
from app.config import settings
from tavily import TavilyClient
import boto3
from app.tools.console_tool import (
    print_info,
    print_warning,
    print_success,
    print_error,
    print_yellow_bg,
)
from .tools import search_tavily
import json

SYSTEM_PROMPT = """
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

Always remember that your purpose is to help agricultural sales representatives build successful, sustainable trading relationships while meeting their immediate business needs.
"""

# The maximum number of recursive calls allowed in the tool_use_demo function.
# This helps prevent infinite loops and potential performance issues.
MAX_RECURSIONS = 5


class PilotAssistantWorkflow(Workflow):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(timeout=1000, *args, **kwargs)
        self.system_prompt = [{"text": SYSTEM_PROMPT}]
        self.tool_config = {
            "tools": [
                {
                    "toolSpec": {
                        "name": "search_tavily",
                        "description": "Search the web for information.",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "The query to search the web for.",
                                    }
                                },
                                "required": ["query"],
                            }
                        },
                    }
                }
            ]
        }
        self.bedrockRuntimeClient = boto3.client(
            "bedrock-runtime",
            region_name=settings.AWS_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    @step
    def prepare_model_input(self, ctx: Context, ev: StartEvent) -> ModelInputEvent:
        asyncio.run(ctx.set("sources", []))
        asyncio.run(ctx.set("answer", ""))
        asyncio.run(ctx.set("agent_action", "THINKING"))
        chat_history = asyncio.run(ctx.get("chat_history", []))
        print_warning(f"chat_history: {chat_history}")
        conversation = []
        for msg in chat_history[-50:]:
            msg_content = str(msg.content);
            if(msg.role != "user"):
                msg_content = msg_content[:100]
            print_warning(f"{msg.role}: {msg_content}")
            conversation.append(
                {"role": str(msg.role.value), "content": [{"text": msg_content}]}
            )
        ctx.write_event_to_stream(StartStreamEvent())
        return ModelInputEvent(input=conversation, max_recursion=MAX_RECURSIONS)

    @step
    def send_to_model(
        self, ctx: Context, ev: ModelInputEvent
    ) -> ModelResponseEvent | StopEvent:
        conversation = ev.input
        max_recursion = ev.max_recursion
        print_warning(f"Conversation-----------------:\n\n {conversation} \n\n")
        if conversation is not None:
            try:
                bedrock_response = self.bedrockRuntimeClient.converse_stream(
                    modelId=settings.AWS_BEDROCK_MODEL,
                    messages=conversation,
                    system=self.system_prompt,
                    toolConfig=self.tool_config,
                )
                block = {
                    "stopReason": "",
                }

                for event in bedrock_response.get("stream"):
                    print_warning(f"Event: {event}")
                    if event.get("messageStart"):
                        pass
                    elif event.get("messageStop"):
                        block["stopReason"] = event.get("messageStop").get("stopReason")
                        if "text" in block:
                            answer = asyncio.run(ctx.get("answer", ""))
                            answer += block["text"]
                            asyncio.run(ctx.set("answer", answer))
                        if block["stopReason"] == "tool_use":
                            block["toolUse"]["input"] = json.loads(
                                block["toolUse"]["input"]
                            )
                        return ModelResponseEvent(
                            model_response=block,
                            conversation=conversation,
                            max_recursion=max_recursion,
                        )
                    elif event.get("contentBlockStart"):
                        contentBlockStart = event.get("contentBlockStart")
                        toolUse = contentBlockStart.get("start").get("toolUse")
                        if toolUse:
                            if "toolUse" not in block:
                                block["toolUse"] = {
                                    "name": "",
                                    "toolUseId": "",
                                    "input": "",
                                }
                            block["toolUse"]["name"] = toolUse.get("name")
                            block["toolUse"]["toolUseId"] = toolUse.get("toolUseId")
                    elif event.get("contentBlockDelta"):
                        contentBlockDelta = event.get("contentBlockDelta")
                        delta = contentBlockDelta.get("delta")
                        if delta.get("text") is not None and delta.get("text") != "":
                            agent_action = asyncio.run(ctx.get("agent_action", ""))
                            if agent_action != "ANSWERING":
                                asyncio.run(ctx.set("agent_action", "ANSWERING"))
                                ctx.write_event_to_stream(
                                    StreamEvent(content="", agent_action="ANSWERING")
                                )
                            if "text" not in block:
                                block["text"] = "\n\n"
                            ctx.write_event_to_stream(
                                StreamEvent(content=delta.get("text"))
                            )
                            block["text"] = block["text"] + delta.get("text")
                        elif delta.get("toolUse"):
                            block["toolUse"]["input"] = block["toolUse"][
                                "input"
                            ] + delta.get("toolUse").get("input")

            except Exception as e:
                print_error(f"Error: {str(e)}")
                return StopEvent(
                    result={
                        "response": "Hi! I ran into a small hiccup while processing your request. Could you please try again? I'm here to help!"
                    }
                )

        else:
            return StopEvent(
                result={
                    "response": "Hi! I ran into a small hiccup while processing your request. Could you please try again? I'm here to help!"
                }
            )

    @step
    def process_model_response(
        self, ctx: Context, ev: ModelResponseEvent
    ) -> ModelToolCallEvent | StopEvent:
        model_response = ev.model_response
        conversation = ev.conversation
        max_recursion = ev.max_recursion

        message = {"role": "assistant", "content": []}
        if "toolUse" in model_response:
            message["content"].append({"toolUse": model_response["toolUse"]})
        if "text" in model_response:
            message["content"].append({"text": model_response["text"]})
        conversation.append(message)

        if max_recursion <= 0:
            print_warning(
                "Warning: Maximum number of recursions reached. Please try again."
            )
            if "text" in message["content"][0]:
                return StopEvent(result={"response": model_response["text"]})
            else:
                return StopEvent(
                    result={
                        "response": "Hi! I ran into a small hiccup while processing your request. Could you please try again? I'm here to help!"
                    }
                )
        else:
            if model_response["stopReason"] == "tool_use":
                return ModelToolCallEvent(
                    message=message,
                    conversation=conversation,
                    max_recursion=max_recursion,
                )

            if model_response["stopReason"] == "end_turn":
                # If the stop reason is "end_turn", print the model's response text, and finish the process
                finale_response = asyncio.run(ctx.get("answer", ""))
                sources = asyncio.run(ctx.get("sources", default=[]))
                if len(sources) > 0:
                    content =  "\n\n##\n\n";
                    finale_response +=  content
                    ctx.write_event_to_stream(StreamEvent(content=content))
                    for source in sources:
                        content = f"\n* [{source['title']}]({source['url']})\n"
                        finale_response += content
                        ctx.write_event_to_stream(StreamEvent(content=content))
                return StopEvent(result={"response": finale_response.strip()})

    @step
    def handle_tool_call(self, ctx: Context, ev: ModelToolCallEvent) -> ModelInputEvent:
        message = ev.message
        conversation = ev.conversation
        max_recursion = ev.max_recursion

        tool_results = []

        for content_block in message["content"]:

            if "toolUse" in content_block:
                # If the content block is a tool use request, forward it to the tool
                tool_response = self._invoke_tool(content_block["toolUse"], ctx)

                # Add the tool use ID and the tool's response to the list of results
                tool_results.append(
                    {
                        "toolResult": {
                            "toolUseId": (tool_response["toolUseId"]),
                            "content": [{"json": tool_response["content"]}],
                        }
                    }
                )
        # Embed the tool results in a new user message
        message = {"role": "user", "content": tool_results}

        # Append the new message to the ongoing conversation
        conversation.append(message)

        # Send the conversation to Amazon Bedrock
        return ModelInputEvent(input=conversation, max_recursion=max_recursion - 1)

    def _invoke_tool(self, payload, ctx: Context):
        """
        Invokes the specified tool with the given payload and returns the tool's response.
        If the requested tool does not exist, an error message is returned.

        :param payload: The payload containing the tool name and input data.
        :return: The tool's response or an error message.
        """

        tool_name = payload["name"]
        ctx.write_event_to_stream(
            ToolCallEvent(tool_name=tool_name, tool_kwargs=payload["input"])
        )

        if tool_name == "search_tavily":
            input_data = payload["input"]
            agent_action = asyncio.run(ctx.get("agent_action", ""))
            if agent_action != "SEARCHING_WEB":
                asyncio.run(ctx.set("agent_action", "SEARCHING_WEB"))
                ctx.write_event_to_stream(
                    StreamEvent(content="", agent_action="SEARCHING_WEB")
                )
            # Invoke the weather tool with the input data provided by
            sources = asyncio.run(ctx.get("sources", default=[]))
            response = search_tavily(input_data)
            for result in response["results"]:
                title = result["title"]
                if title == "PDF":
                    # Extract filename from URL path
                    url_parts = result["url"].split("/")
                    title = url_parts[-1]
                sources.append({"title": title, "url": result["url"]})
            asyncio.run(ctx.set("sources", sources))
            ctx.write_event_to_stream(
                ToolCallResultEvent(result=response, tool_name=tool_name)
            )
        else:
            error_message = (
                f"The requested tool with name '{tool_name}' does not exist."
            )
            response = {"error": "true", "message": error_message}
            ctx.write_event_to_stream(ToolCallErrorEvent(error=error_message))
        return {"toolUseId": payload["toolUseId"], "content": response}
