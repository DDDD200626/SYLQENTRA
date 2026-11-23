from app.agents.automation.automation_agent import AutomationAgent
from app.agents.base.base_agent import BaseAgent
from app.agents.data.data_agent import DataAgent
from app.agents.developer.developer_agent import DeveloperAgent
from app.agents.document.document_agent import DocumentAgent
from app.agents.manager.manager_agent import ManagerAgent
from app.agents.research.research_agent import ResearchAgent
from app.agents.review.review_agent import ReviewAgent
from app.ai_models.model_manager import ModelManager

AGENT_CLASSES: dict[str, type[BaseAgent]] = {
    ManagerAgent.role: ManagerAgent,
    ResearchAgent.role: ResearchAgent,
    DataAgent.role: DataAgent,
    DeveloperAgent.role: DeveloperAgent,
    DocumentAgent.role: DocumentAgent,
    ReviewAgent.role: ReviewAgent,
    AutomationAgent.role: AutomationAgent,
}


def create_agent(role: str, model_manager: ModelManager, provider: str, model: str) -> BaseAgent:
    agent_class = AGENT_CLASSES.get(role)
    if agent_class is None:
        known = ", ".join(sorted(AGENT_CLASSES))
        raise ValueError(f"Unknown agent role '{role}'. Known roles: {known}")
    return agent_class(model_manager, provider, model)
