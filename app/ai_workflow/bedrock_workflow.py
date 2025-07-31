# """
# This demo illustrates a tool use scenario using Amazon Bedrock's Converse API and a weather tool.
# The script interacts with a foundation model on Amazon Bedrock to provide weather information based on user
# input. It uses the Open-Meteo API (https://open-meteo.com) to retrieve current weather data for a given location.
# """

# import boto3
# import logging
# from enum import Enum
# from app.config import settings
# from tavily import TavilyClient
# from llama_index.core.memory import BaseMemory
# from llama_index.core.workflow.context import Context
# from app.tools.console_tool import (
#     print_info,
#     print_warning,
#     print_success,
#     print_error,
#     print_yellow_bg,
# )

# logging.basicConfig(level=logging.INFO, format="%(message)s")

# AWS_REGION = "us-east-1"


# # For the most recent list of models supported by the Converse API's tool use functionality, visit:
# # https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html



# # Set the model ID, e.g., Claude 3 Haiku.
# MODEL_ID = SupportedModels.CLAUDE_HAIKU.value

# SYSTEM_PROMPT = """
# You are X-Pilot Assistant, an AI specifically designed to support agricultural trading sales representatives. Your goal is to provide accurate, practical, and actionable information that helps agricultural sales professionals succeed in their daily work. You have deep expertise in agricultural commodities, international trade logistics, market analysis, sales communication, and relationship management within the agricultural sector.

# Core Capabilities and Approach
# Customer & Market Research
# Provide detailed company verification guidance including how to check import/export history, certifications, and company reliability markers
# Deliver current market insights on agricultural commodities with price trends, seasonal factors, and regional variations
# Analyze market conditions affecting specific products (cashews, rice, pepper, etc.) with evidence-based insights
# Format market data in clear, actionable tables and bullet points when appropriate

# Sales Communication Support
# Improve communication by enhancing message tone, clarity, and professionalism
# Assist with translation and cultural nuances in international agricultural trade
# Draft customized product offers, quotations, and proposals using industry-standard terminology
# Structure communications to highlight key value propositions relevant to specific agricultural products
# Include both formal and relationship-building elements appropriate to the sales context
# Product & Logistics Knowledge
# Explain documentation requirements for agricultural exports to specific markets
# Provide clear guidance on phytosanitary certificates, quality certifications, and customs documentation
# Simplify complex trade terms (INCOTERMS) using practical examples relevant to agricultural trade
# Offer product-specific shipping and logistics recommendations with consideration for perishability, temperature control, and preservation
# Deal Closing Support
# Articulate key selling points for agricultural products with emphasis on origin, quality metrics, certifications, and competitive advantages
# Prepare persuasive responses to common buyer objections regarding price, delivery time, and quality assurance
# Suggest effective negotiation techniques specific to agricultural commodity trading
# Identify red flags in potential deals and offer risk mitigation strategies
# Performance & Strategy
# Summarize and structure sales conversations into actionable insights for CRM entry
# Recommend follow-up strategies based on conversation content and buyer signals
# Share best practices for agricultural trade negotiations with cultural considerations
# Provide templates for tracking sales performance specific to agricultural commodities
# Response Style and Format
# Always cite sources: Clearly indicate the origin of information with links to the sources
# Be transparent about confidence levels: Distinguish between verified facts, industry standards, and professional judgments
# Include reference links: When providing market data or regulatory information, always include links to official sources 
# Be concise yet thorough: Sales representatives are busy; provide actionable information efficiently
# Use industry terminology: Demonstrate familiarity with agricultural trade language while remaining accessible
# Provide visual organization: Use formatting (tables, bullet points) to make information easy to scan and apply
# Include practical examples: Connect advice to real-world agricultural trading scenarios
# Maintain a professional, supportive tone: Be a knowledgeable colleague rather than a generic assistant
# Structure responses logically: Present information in order of importance to the sales process
# Balance detail with actionability: Provide enough information to be useful without overwhelming
# Consider timing in the sales cycle: Tailor advice based on whether the rep is prospecting, negotiating, or closing
# Specialized Knowledge Areas
# Deep understanding of agricultural commodities and their quality parameters
# Familiarity with international agricultural trade regulations and documentation
# Knowledge of price factors and seasonal variations in agricultural markets
# Awareness of supply chain considerations for perishable goods
# Understanding of common certification standards in agricultural trade (Organic, Fair Trade, GlobalGAP, etc.)
# Familiarity with cultural considerations in international agricultural business
# Knowledge of typical payment terms and financial instruments in agricultural trade
# When responding to queries, draw on this specialized knowledge while maintaining a practical focus on helping the sales representative succeed in their immediate task and long-term relationship building with agricultural buyers and suppliers.
# Response Examples
# When asked about market prices: "The current market price for Vietnamese cashew kernels (W320) is $3.20-3.40/kg FOB Ho Chi Minh City, showing a 5% increase since last month due to limited supply from early harvest. Key factors affecting this price include: [list factors]. Consider highlighting these market dynamics when discussing with your buyer to justify your pricing structure."
# When asked about documentation: "To export organic rice from Thailand to Germany, you'll need: 1) Commercial Invoice, 2) Packing List, 3) Certificate of Origin, 4) Phytosanitary Certificate, 5) Organic Certification recognized by EU, 6) EUR.1 Movement Certificate to benefit from preferential duties, and 7) Bill of Lading. The most frequent delay occurs with the phytosanitary certificate, which requires inspection at least 7 days before shipment - plan accordingly to avoid postponing your vessel booking."
# When asked about responding to a buyer: "Based on this buyer's message expressing concerns about moisture content in the coffee beans, I suggest this response structure:
# Acknowledge their quality concerns directly
# Explain your quality control process specifically for moisture (include exact measurement methods)
# Offer documentation proof (moisture meter readings, lab results)
# Propose a solution (replacement, discount, or third-party verification)
# Reinforce relationship value Here's a draft response incorporating these elements: [draft message]"

# Tool usage: tavily_search

# Always remember that your purpose is to help agricultural sales representatives build successful, sustainable trading relationships while meeting their immediate business needs.
# """

# # The maximum number of recursive calls allowed in the tool_use_demo function.
# # This helps prevent infinite loops and potential performance issues.
# MAX_RECURSIONS = 5
# tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)

# def search_tavily(input_data):
#     """
#     Fetches weather data for the given latitude and longitude using the Open-Meteo API.
#     Returns the weather data or an error message if the request fails.

#     :param input_data: The input data containing the latitude and longitude.
#     :return: The weather data or an error message.
#     """

#     try:
#         response = tavily_client.search(input_data["query"])
#         print(response)
#         return response
#     except Exception as e:
#         return {"error": type(e), "message": str(e)}


# class ToolUseDemo:
#     """
#     Demonstrates the tool use feature with the Amazon Bedrock Converse API.
#     """

#     def __init__(self):
#         # Prepare the system prompt
#         self.system_prompt = [{"text": SYSTEM_PROMPT}]

#         # Prepare the tool configuration with the weather tool's specification
#         self.tool_config = {
#             "tools": [
#                 {
#                     "toolSpec": {
#                         "name": "search_tavily",
#                         "description": "Search the web for information.",
#                         "inputSchema": {
#                             "json": {
#                                 "type": "object",
#                                 "properties": {
#                                     "query": {
#                                         "type": "string",
#                                         "description": "The query to search the web for.",
#                                     }
#                                 },
#                                 "required": ["query"],
#                             }
#                         },
#                     }
#                 }
#             ]
#         }
#         print(self.tool_config)

#         # Create a Bedrock Runtime client in the specified AWS Region.
#         self.bedrockRuntimeClient = boto3.client(
#             "bedrock-runtime",
#             region_name=settings.AWS_REGION_NAME,
#             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
#         )

#     def run(self, conversation: list):
#         """
#         Starts the conversation with the user and handles the interaction with Bedrock.
#         """
#         # Start with an emtpy conversation

#         if conversation is not None:
#             # Create a new message with the user input and append it to the conversation

#             # Send the conversation to Amazon Bedrock
#             bedrock_response = self._send_conversation_to_bedrock(conversation)

#             # Recursively handle the model's response until the model has returned
#             # its final response or the recursion counter has reached 0
#             self._process_model_response(
#                 bedrock_response, conversation, max_recursion=MAX_RECURSIONS
#             )

#     def _send_conversation_to_bedrock(self, conversation):
#         """
#         Sends the conversation, the system prompt, and the tool spec to Amazon Bedrock, and returns the response.

#         :param conversation: The conversation history including the next message to send.
#         :return: The response from Amazon Bedrock.
#         """

#         # Send the conversation, system prompt, and tool configuration, and return the response
#         return self.bedrockRuntimeClient.converse(
#             modelId=MODEL_ID,
#             messages=conversation,
#             system=self.system_prompt,
#             toolConfig=self.tool_config,
#         )

#     def _process_model_response(
#         self, model_response, conversation, max_recursion=MAX_RECURSIONS
#     ):
#         """
#         Processes the response received via Amazon Bedrock and performs the necessary actions
#         based on the stop reason.

#         :param model_response: The model's response returned via Amazon Bedrock.
#         :param conversation: The conversation history.
#         :param max_recursion: The maximum number of recursive calls allowed.
#         """

#         if max_recursion <= 0:
#             # Stop the process, the number of recursive calls could indicate an infinite loop
#             logging.warning(
#                 "Warning: Maximum number of recursions reached. Please try again."
#             )
#             exit(1)

#         # Append the model's response to the ongoing conversation
#         message = model_response["output"]["message"]
#         conversation.append(message)

#         print_warning(f"Model response: {model_response}")

#         if model_response["stopReason"] == "tool_use":
#             # If the stop reason is "tool_use", forward everything to the tool use handler
#             self._handle_tool_use(message, conversation, max_recursion)

#         if model_response["stopReason"] == "end_turn":
#             # If the stop reason is "end_turn", print the model's response text, and finish the process
#             print(message["content"][0]["text"])
#             return

#     def _handle_tool_use(
#         self, model_response, conversation, max_recursion=MAX_RECURSIONS
#     ):
#         """
#         Handles the tool use case by invoking the specified tool and sending the tool's response back to Bedrock.
#         The tool response is appended to the conversation, and the conversation is sent back to Amazon Bedrock for further processing.

#         :param model_response: The model's response containing the tool use request.
#         :param conversation: The conversation history.
#         :param max_recursion: The maximum number of recursive calls allowed.
#         """

#         # Initialize an empty list of tool results
#         tool_results = []

#         # The model's response can consist of multiple content blocks
#         for content_block in model_response["content"]:
#             if "text" in content_block:
#                 # If the content block contains text, print it to the console
#                 print(content_block["text"])

#             if "toolUse" in content_block:
#                 # If the content block is a tool use request, forward it to the tool
#                 tool_response = self._invoke_tool(content_block["toolUse"])

#                 # Add the tool use ID and the tool's response to the list of results
#                 tool_results.append(
#                     {
#                         "toolResult": {
#                             "toolUseId": (tool_response["toolUseId"]),
#                             "content": [{"json": tool_response["content"]}],
#                         }
#                     }
#                 )

#         # Embed the tool results in a new user message
#         message = {"role": "user", "content": tool_results}

#         # Append the new message to the ongoing conversation
#         conversation.append(message)

#         # Send the conversation to Amazon Bedrock
#         response = self._send_conversation_to_bedrock(conversation)

#         # Recursively handle the model's response until the model has returned
#         # its final response or the recursion counter has reached 0
#         self._process_model_response(response, conversation, max_recursion - 1)

#     def _invoke_tool(self, payload):
#         """
#         Invokes the specified tool with the given payload and returns the tool's response.
#         If the requested tool does not exist, an error message is returned.

#         :param payload: The payload containing the tool name and input data.
#         :return: The tool's response or an error message.
#         """
#         tool_name = payload["name"]
#         print(tool_name)

#         if tool_name == "search_tavily":
#             input_data = payload["input"]
#             print(tool_name, input_data)

#             # Invoke the weather tool with the input data provided by
#             response = search_tavily(input_data)
#         else:
#             error_message = (
#                 f"The requested tool with name '{tool_name}' does not exist."
#             )
#             response = {"error": "true", "message": error_message}

#         return {"toolUseId": payload["toolUseId"], "content": response}

