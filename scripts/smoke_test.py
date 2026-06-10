from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from item_reviser.agents.pipeline import ItemReviserPipeline  # noqa: E402
from item_reviser.models.base import BaseLLM  # noqa: E402
from item_reviser.schemas import SurveyItem  # noqa: E402


class SmokeLLM(BaseLLM):
    backend_name = "smoke"

    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def generate(
        self,
        prompt: str,
        *,
        timeout_seconds: float | None = None,
        **kwargs,
    ) -> str:
        _ = prompt, timeout_seconds, kwargs
        self.calls += 1
        if self.calls == 1:
            return json.dumps(
                {
                    "errors": [
                        {
                            "category": "leading_question",
                            "severity": "high",
                            "explanation": "The wording signals that agreement is expected.",
                            "evidence": "Don't you agree",
                            "checker": "llm",
                        }
                    ]
                }
            )
        return json.dumps(
            {
                "question": "To what extent do you support or oppose stricter environmental regulations?",
                "response_options": [
                    "Strongly oppose",
                    "Somewhat oppose",
                    "Neither support nor oppose",
                    "Somewhat support",
                    "Strongly support",
                ],
                "revision_notes": ["Reworded the leading item as a balanced support question."],
                "changed": True,
            }
        )


def main() -> None:
    item = SurveyItem(question="Don’t you agree that stricter environmental regulations are necessary?")
    result = ItemReviserPipeline(model=SmokeLLM()).run(item)
    assert "leading_question" in result.predicted_categories()
    print("Smoke test passed.")


if __name__ == "__main__":
    main()
