from app.agents.base.base_agent import BaseAgent


class DocumentAgent(BaseAgent):
    role = "document"
    description = "분석 결과를 문서 초안으로 정리한다."
    allowed_tools = ("document_draft",)
    system_prompt = (
        "You are the SYLQENTRA Document Agent. Turn the supplied analysis into a structured draft. "
        "Keep every number identical to the source text. Do not add figures that were not provided."
    )
