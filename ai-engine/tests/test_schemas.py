import pytest
from pydantic import ValidationError

from ai_engine.schemas import ExplanationOutput


def test_accepts_valid_prose() -> None:
    out = ExplanationOutput(
        simple_explanation="This is a plain-English explanation of the problem, long enough to pass validation.",
        technical_explanation="This is a technical explanation referencing the relevant mechanism precisely enough.",
    )
    assert "plain-English" in out.simple_explanation


@pytest.mark.parametrize(
    "simple,technical",
    [
        ("too short", "This is a technical explanation referencing the relevant mechanism precisely enough."),
        ("This is a plain-English explanation of the problem, long enough to pass validation.", "too short"),
    ],
)
def test_rejects_too_short(simple: str, technical: str) -> None:
    with pytest.raises(ValidationError):
        ExplanationOutput(simple_explanation=simple, technical_explanation=technical)


def test_rejects_html() -> None:
    with pytest.raises(ValidationError):
        ExplanationOutput(
            simple_explanation="<script>alert(1)</script> this is long enough to pass the length check on its own.",
            technical_explanation="This is a technical explanation referencing the relevant mechanism precisely enough.",
        )


def test_rejects_code_fences() -> None:
    with pytest.raises(ValidationError):
        ExplanationOutput(
            simple_explanation="This is a plain-English explanation of the problem, long enough to pass validation.",
            technical_explanation="```js\nalert(1)\n``` and this text pads it out past the minimum length requirement.",
        )
