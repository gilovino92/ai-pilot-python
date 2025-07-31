from app.config import settings
from typing import Optional
from llama_index.llms.bedrock_converse import BedrockConverse
from llama_index.llms.openai import OpenAI


def summarizer_llm():
    return OpenAI(model_name="gpt-4o-mini",api_key=settings.OPENAI_API_KEY, max_tokens=256)

def llm(system_prompt: Optional[str] = None, args: Optional[dict] = {}):
    llm = settings.LLM;
    print(llm)
    match llm:
        case "openai":
            return OpenAI(model=settings.OPENAI_MODEL, api_key=settings.OPENAI_API_KEY, system_prompt=system_prompt, temperature=0, **args)
        case "bedrock":
            return BedrockConverse(
                model=settings.AWS_BEDROCK_MODEL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION_NAME,
                system_prompt=system_prompt, temperature=0,trace="ENABLED", **args)