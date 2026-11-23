from app.agents.base.base_agent import BaseAgent


class ReviewAgent(BaseAgent):
    role = "review"
    description = "결과의 누락과 모순을 검증한다."
    allowed_tools = ()
    system_prompt = (
        "You are the SYLQENTRA Review Agent. Check the draft for missing inputs, changed numbers, "
        "and unsupported claims. List findings before giving a pass or fail. Do not rewrite the whole draft."
    )
