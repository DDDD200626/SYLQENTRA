from app.agents.base.base_agent import BaseAgent


class AutomationAgent(BaseAgent):
    role = "automation"
    description = "허용된 외부 작업의 실행 조건을 확인한다."
    allowed_tools = ("email", "slack")
    system_prompt = (
        "You are the SYLQENTRA Automation Agent. You cannot send email or post to Slack in this step. "
        "If an allowed tool is requested, describe the exact action that should wait for approval. "
        "If approval is not included in the task, stop and request approval."
    )
