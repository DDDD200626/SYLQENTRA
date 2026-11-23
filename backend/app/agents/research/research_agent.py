from app.agents.base.base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    role = "research"
    description = "자료 검색과 요약을 담당한다."
    allowed_tools = ("web_search", "document_search")
    system_prompt = (
        "You are the SYLQENTRA Research Agent. Summarize only the supplied material. "
        "Mark any claim that is not present in the task input as unverified. "
        "Do not pretend a search tool ran unless its result is included in the task."
    )
