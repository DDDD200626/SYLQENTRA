from app.agents.base.base_agent import BaseAgent


class ManagerAgent(BaseAgent):
    role = "manager"
    description = "업무를 분석하고 전문 Agent에 배분할 계획을 만든다."
    allowed_tools = ()
    system_prompt = (
        "You are the SYLQENTRA Manager Agent. Break the request into specialist tasks. "
        "Name the agent role for each task: research, data, developer, document, review, or automation. "
        "Do not claim that any specialist task has already been completed."
    )
