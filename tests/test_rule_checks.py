from item_reviser.checks.registry import run_all_checks
from item_reviser.schemas import SurveyItem


def test_leading_question_detected():
    item = SurveyItem(question="Don’t you agree that stricter environmental regulations are necessary?")
    categories = {r.category for r in run_all_checks(item)}
    assert "leading_question" in categories


def test_good_satisfaction_item_not_flagged():
    item = SurveyItem(
        question="How satisfied or dissatisfied are you with your current job?",
        response_options=[
            "Very dissatisfied",
            "Somewhat dissatisfied",
            "Neither satisfied nor dissatisfied",
            "Somewhat satisfied",
            "Very satisfied",
        ],
    )
    categories = {r.category for r in run_all_checks(item)}
    assert not categories
