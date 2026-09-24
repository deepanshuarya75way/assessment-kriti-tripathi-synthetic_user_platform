"""Agent / pipeline logic tests (spec §11, §13). Uses the fake provider."""

from app.agents.persona_agent import _is_duplicate
from app.agents.response_agent import _reconcile
from app.graph.graph import run_pipeline
from app.graph.schemas import Persona, PersonaSurveyResponse, SurveyAnswer, SurveyQuestion


def _persona(name, occ, savvy):
    return Persona(
        id="p",
        name=name,
        age=30,
        occupation=occ,
        background="b",
        personality_traits=["a"],
        behavioral_patterns=["x"],
        psychological_profile="p",
        goals=["g"],
        pain_points=["pp"],
        tech_savviness=savvy,
        communication_style="c",
        persona_summary="s",
    )


def test_duplicate_detection_by_name():
    existing = [_persona("Riya", "Student", "low")]
    assert _is_duplicate(_persona("riya", "Engineer", "high"), existing)


def test_duplicate_detection_by_occupation_and_savviness():
    existing = [_persona("Riya", "Student", "low")]
    assert _is_duplicate(_persona("Sam", "student", "low"), existing)
    assert not _is_duplicate(_persona("Sam", "student", "high"), existing)


def test_response_reconcile_backfills_missing_answers():
    questions = [
        SurveyQuestion(id="q1", text="a", question_type="yes_no", rationale="r"),
        SurveyQuestion(id="q2", text="b", question_type="open_ended", rationale="r"),
    ]
    partial = PersonaSurveyResponse(
        persona_id="p1",
        answers=[
            SurveyAnswer(question_id="q1", answer="yes", sentiment="positive", confidence=0.9)
        ],
    )
    fixed = _reconcile(partial, questions)
    assert [a.question_id for a in fixed.answers] == ["q1", "q2"]
    assert fixed.answers[1].confidence == 0.0  # placeholder for the missing one


def test_response_reconcile_drops_extra_answers():
    questions = [SurveyQuestion(id="q1", text="a", question_type="yes_no", rationale="r")]
    resp = PersonaSurveyResponse(
        persona_id="p1",
        answers=[
            SurveyAnswer(question_id="q1", answer="yes", sentiment="positive", confidence=0.5),
            SurveyAnswer(question_id="q99", answer="junk", sentiment="neutral", confidence=0.5),
        ],
    )
    fixed = _reconcile(resp, questions)
    assert len(fixed.answers) == 1 and fixed.answers[0].question_id == "q1"


def test_full_pipeline_counts_are_consistent():
    state = run_pipeline(
        "A product for testing",
        "Test users",
        "Decide features",
        num_personas=3,
        num_questions=4,
        run_id="t",
    )
    assert len(state["personas"]) == 3
    assert len(state["survey_questions"]) == 4
    assert len(state["survey_responses"]) == 3
    # every persona answered exactly every question
    for r in state["survey_responses"]:
        assert len(r.answers) == 4
    assert state["insight_report"].executive_summary
