#!/usr/bin/env python3
"""Rebuild 1404 mathematics question crops directly from the official PDF."""

import json
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "assets/source/arshad_bargh_1404_1251.pdf"
DATA = ROOT / "data/questions/exam_1404.json"

# Hand-checked boundaries on the 150-DPI official booklet pages.  Automatic
# marker detection is unreliable on pages that mix English LTR and Persian RTL
# numbering, so these coordinates deliberately preserve extra white space.
PAGE_BOUNDARIES = {
    6: [760, 1200, 1755],
    7: [140, 500, 900, 1200, 1755],
    8: [140, 480, 760, 930, 1160, 1755],
    9: [140, 470, 870, 1260, 1755],
}


def render_page(page_number, target):
    subprocess.run(
        [
            "pdftoppm", "-f", str(page_number), "-l", str(page_number),
            "-r", "150", "-png", "-singlefile", str(PDF), str(target),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    exam = json.loads(DATA.read_text(encoding="utf-8"))
    math_questions = [q for q in exam["questions"] if 26 <= q["number"] <= 40]
    by_page = defaultdict(list)
    for question in math_questions:
        by_page[question["source_page"]].append(question)

    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        for page_number, questions in sorted(by_page.items()):
            questions.sort(key=lambda item: item["number"])
            prefix = directory / f"page_{page_number}"
            render_page(page_number, prefix)
            page = Image.open(prefix.with_suffix(".png")).convert("RGB")
            boundaries = PAGE_BOUNDARIES[page_number]
            if len(boundaries) != len(questions) + 1:
                raise ValueError(f"Boundary count mismatch on page {page_number}")
            top_margin = max(30, page.height // 55)
            bottom_gap = max(6, page.height // 220)
            for index, question in enumerate(questions):
                if "image" not in question:
                    continue
                top = max(0, boundaries[index] - top_margin)
                bottom = (
                    page.height
                    if index + 1 == len(questions)
                    else max(top + 180, boundaries[index + 1] - bottom_gap)
                )
                crop = page.crop((0, top, page.width, bottom))
                target = ROOT / question["image"]
                temporary = target.with_suffix(".tmp.png")
                crop.save(temporary, "PNG", optimize=True)
                temporary.replace(target)


if __name__ == "__main__":
    main()
