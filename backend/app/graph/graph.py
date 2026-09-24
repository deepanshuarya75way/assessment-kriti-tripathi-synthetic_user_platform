"""
LangGraph StateGraph wiring:

    persona_agent -> survey_agent -> response_agent -> insight_agent -> END

The graph is compiled ONCE at import time (``PIPELINE``) rather than rebuilt on
every call. The original code rebuilt the graph — and a fresh in-memory
``MemorySaver`` — on every ``run_pipeline`` call, so nothing ever persisted
across calls (audit bug B1). Durable, cross-run recovery is now the database's
job (see docs/design-decisions.md); a checkpointer is only useful within a
single run and would add no durability here, so it is intentionally omitted.
"""

from langgraph.graph import END, StateGraph

from app.agents.insight_agent import insight_agent_node
from app.agents.persona_agent import persona_agent_node
from app.agents.response_agent import response_agent_node
from app.agents.survey_agent import survey_agent_node
from app.graph.state import GraphState


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("persona_agent", persona_agent_node)
    graph.add_node("survey_agent", survey_agent_node)
    graph.add_node("response_agent", response_agent_node)
    graph.add_node("insight_agent", insight_agent_node)

    graph.set_entry_point("persona_agent")
    graph.add_edge("persona_agent", "survey_agent")
    graph.add_edge("survey_agent", "response_agent")
    graph.add_edge("response_agent", "insight_agent")
    graph.add_edge("insight_agent", END)
    return graph.compile()


# Compiled once and reused across runs.
PIPELINE = build_graph()


def run_pipeline(
    product_description: str,
    target_audience: str,
    research_goal: str,
    num_personas: int = 5,
    num_questions: int = 6,
    run_id: str = "run",
) -> GraphState:
    initial_state: GraphState = {
        "product_description": product_description,
        "target_audience": target_audience,
        "research_goal": research_goal,
        "num_personas": num_personas,
        "num_questions": num_questions,
        "run_id": run_id,
        "log": [],
    }
    return PIPELINE.invoke(initial_state)
