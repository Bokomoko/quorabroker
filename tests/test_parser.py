from __future__ import annotations

from quorabroker.parser import extract_question_answer


def test_extract_question_answer(sample_html: str) -> None:
    data = extract_question_answer(sample_html)
    assert data["question"] == "What is Python?"
    assert data["answer"].startswith("Python is a programming language")
