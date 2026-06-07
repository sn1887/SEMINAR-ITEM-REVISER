from item_reviser.schemas import SurveyItem


def test_survey_item_roundtrip():
    data = {"id": "x", "question": "Q?", "response_options": ["Yes", "No"], "known_errors": []}
    item = SurveyItem.from_dict(data)
    assert item.to_dict()["id"] == "x"
    assert item.response_options == ["Yes", "No"]
