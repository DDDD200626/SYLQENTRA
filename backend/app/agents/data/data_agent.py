from app.agents.base.base_agent import BaseAgent


class DataAgent(BaseAgent):
    role = "data"
    description = "표와 수치를 계산하고 해석한다."
    allowed_tools = ("tabular_data",)
    system_prompt = (
        "You are the SYLQENTRA Data Agent. Use only numbers present in the task input. "
        "Show the calculation for every derived figure and separate observations from recommendations. "
        "If a required number is missing, say which input is missing."
    )
