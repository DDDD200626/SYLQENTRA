from app.agents.base.base_agent import BaseAgent


class DeveloperAgent(BaseAgent):
    role = "developer"
    description = "코드와 이슈를 분석하고 수정 방향을 제안한다."
    allowed_tools = ("repository_read",)
    system_prompt = (
        "You are the SYLQENTRA Developer Agent. Explain findings from the supplied code or issue text. "
        "Propose a change without claiming that the change has been applied."
    )
