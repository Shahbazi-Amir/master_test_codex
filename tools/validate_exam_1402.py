#!/usr/bin/env python3
"""Validate the complete 1402 exam dataset and presentation assets."""

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/questions/exam_1402.json"


def main():
    exam = json.loads(DATA.read_text(encoding="utf-8"))
    questions = exam["questions"]
    if len(questions) != 133:
        raise ValueError(f"Expected 133 questions, found {len(questions)}")
    for expected, question in enumerate(questions, 1):
        if question["number"] != expected:
            raise ValueError(f"Question sequence breaks at {expected}")
        if question.get("correct_answer") not in {1, 2, 3, 4}:
            raise ValueError(f"Invalid answer for question {expected}")
        if question.get("text"):
            if len(question.get("choice_texts", [])) != 4:
                raise ValueError(f"Question {expected} does not have four text choices")
            continue
        image_value = question.get("image")
        if not image_value:
            raise ValueError(f"Question {expected} has neither text nor image")
        image_path = ROOT / image_value
        if not image_path.exists():
            raise ValueError(f"Missing image for question {expected}")
        width, height = Image.open(image_path).size
        if width < 1000 or height < 400:
            raise ValueError(f"Question {expected} image is too small: {width}x{height}")
    print("1402 exam validation passed: 133 questions")


if __name__ == "__main__":
    main()
