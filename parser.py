"""HTML parsing utilities for extracting question & answer text."""
from __future__ import annotations

from bs4 import BeautifulSoup  # type: ignore

QUESTION_SELECTOR = "div.puppeteer_test_question_title"
ANSWER_SELECTOR = "p.q-text.qu-display--block.qu-wordBreak--break-word.qu-textAlign--start"


def extract_question_answer(html: str) -> dict[str, str | None]:
    soup = BeautifulSoup(html, "html.parser")
    q_el = soup.select_one(QUESTION_SELECTOR)
    a_el = soup.select_one(ANSWER_SELECTOR)
    question = q_el.get_text(strip=True) if q_el else None
    answer = a_el.get_text("\n", strip=True) if a_el else None
    return {"question": question, "answer": answer}
