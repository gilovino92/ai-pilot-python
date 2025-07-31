from app.config import settings
from llama_index.core.tools import FunctionTool
from llama_index.core.workflow import Context
import httpx
import json
from typing import Annotated
from pydantic import BaseModel

class GetCompanyInfoPayload(BaseModel):
    company_name: str

async def get_company_info(
    ctx: Context,
    company_name: Annotated[str, "This field describes the company name"],
) -> dict:
    user_id = await ctx.get("user_id")
    tenant_url = settings.TENANT_URL
    tenant_api_key = settings.TENANT_API_KEY

    headers = {
        "X-API-Key": f"{tenant_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        search_response = await client.get(
            f"{tenant_url}/v1/internal/customers/search?",
            params={"user_id": user_id, "name": company_name},
            headers=headers,
        )
        if search_response.status_code != 200:
            return "There is no company with this name."
        return json.dumps(search_response.json())


get_companies_by_name = FunctionTool.from_defaults(
    async_fn=get_company_info,
    name="get_companies_by_name",
    description="Get the current companies by name",
    fn_schema=GetCompanyInfoPayload,
)
