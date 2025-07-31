from app.config import settings
from tavily import TavilyClient

tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)

def search_tavily(input_data):
    try:
        response = tavily_client.search(input_data["query"])
        return response
    except Exception as e:
        return {"error": type(e), "message": str(e)}