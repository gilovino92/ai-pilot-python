from app.config import settings
from llama_index.core.tools import FunctionTool
from llama_index.core.workflow import Context
from typing import Annotated, Optional
from pydantic import BaseModel
import httpx
import json

class UpdateCompanyInfoPayload(BaseModel):
    company_id: str
    phone_number: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    note: Optional[str] = None

async def update_company_info(
    ctx: Context,
    company_id: Annotated[
        str, "This field describes the company id"
    ],
    phone_number: Annotated[Optional[str], "new phone number of the company that user want to update"] = None,
    address: Annotated[Optional[str], "new address of the company that user want to update"] = None,
    email: Annotated[Optional[str], "new email of the company that user want to update"] = None,
    industry: Annotated[Optional[str], "new industry of the company that user want to update"] = None,
    website: Annotated[Optional[str], "This field describes the company website"] = None,
    note: Annotated[Optional[str], "This field describes the company note"] = None
) -> dict:
    user_id = await ctx.get("user_id")
    tenant_url = settings.TENANT_URL
    tenant_api_key = settings.TENANT_API_KEY

    headers = {
        "X-API-Key": f"{tenant_api_key}",
        "Content-Type": "application/json",
    }

    args = {
       "phone_number": phone_number,
       "address": address,
       "email": email,
       "industry": industry,
       "website": website,
       "note": note
    }
    
    payload = {
        "user_id": user_id,
        "fields": {
            k: v for k, v in args.items() if v
        }
    }
    if company_id:
        async with httpx.AsyncClient() as client:
            update_response = await client.patch(
                f"{tenant_url}/v1/internal/customers/{company_id}",
                headers=headers,
                json=payload
            )
            if update_response.status_code != 200:
                return "There was an error while updating the company."
            return json.dumps(update_response.json())
        
       
update_company = FunctionTool.from_defaults(
    async_fn=update_company_info,
    name="update_company",
    description="Update the company info by id",
    fn_schema=UpdateCompanyInfoPayload
)
