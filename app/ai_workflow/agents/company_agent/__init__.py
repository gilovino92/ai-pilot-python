from  llama_index.core.agent.workflow import FunctionAgent
from app.ai_workflow.LLMs import llm
from app.ai_workflow.agents.company_agent.tools.get_company import get_companies_by_name
from app.ai_workflow.agents.company_agent.tools.update_company import update_company

COMPANY_AGENT_NAME = "company_agent"

COMPANY_AGENT_DESCRIPTION = "Call this tool to do tasks related to Company like Get company info or Update company info"

COMPANY_AGENT_SYSTEM_PROMPT = """
You are CompanyAgent, a specialized assistant whose sole responsibility is to execute TOOLS for managing customer (company) records—instead of answering questions directly.

WORKFLOW

1. Check for Existing Company
Immediately call get_companies_by_name with the provided name to see if it exists in the database.

If multiple results are returned, ask:

“I found these companies in our database: [list names]. Which one would you like to work with?

2. Identify Applicable Tool
Choose the correct TOOL (get_company, create_company, update_company, delete_company) based solely on the user’s intent.

3. Validate Parameters
Use only arguments explicitly provided by the user.
Do not invent or infer missing data.

If any required fields are missing or ambiguous, ask for clarification.

4. Execute or Delegate
After receiving explicit confirmation, invoke the selected TOOL with exactly the supplied arguments.

RULES
No Hallucinations: Only use parameters the user provides.
""" 

COMPANY_AGENT_LLM = llm(system_prompt=COMPANY_AGENT_SYSTEM_PROMPT)

def get_company_agent(can_handoff_to: list[str] = []):
    return FunctionAgent(
            name=COMPANY_AGENT_NAME,
            description=COMPANY_AGENT_DESCRIPTION,
            system_prompt=COMPANY_AGENT_SYSTEM_PROMPT,
            llm=COMPANY_AGENT_LLM,
            tools=[get_companies_by_name, update_company],
            can_handoff_to=can_handoff_to,
    )



__all__ = [get_company_agent]