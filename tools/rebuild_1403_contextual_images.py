#!/usr/bin/env python3
"""Rebuild 1403 technical-question images with adjacent-question context."""

import argparse
import json
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

from PIL import Image

from crop_question_images import marker_starts


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "assets/source/arshad_bargh_1403_1251.pdf"
DATA = ROOT / "data/questions/exam_1403.json"

# The first mathematics page follows an English question, which confuses the
# mixed-margin detector. These starts were checked against the official page.
MANUAL_PAGE_6 = {26: 430, 27: 790, 28: 1030, 29: 1270}
MANUAL_PAGE_19 = {71: 210, 72: 665, 73: 1120}


def render_page(number, directory):
    prefix = directory / f"page_{number}"
    subprocess.run(
        ["pdftoppm", "-f", str(number), "-l", str(number), "-r", "150",
         "-png", "-singlefile", str(PDF), str(prefix)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return prefix.with_suffix(".png")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("first", type=int)
    parser.add_argument("last", type=int)
    args = parser.parse_args()

    data = json.loads(DATA.read_text(encoding="utf-8"))
    technical = [q for q in data["questions"] if q["number"] >= 26 and q.get("image")]
    targets = {q["number"] for q in technical if args.first <= q["number"] <= args.last}
    by_page = defaultdict(list)
    for question in technical:
        by_page[question["source_page"]].append(question)

    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        for page_number, questions in sorted(by_page.items()):
            if not any(q["number"] in targets for q in questions):
                continue
            questions.sort(key=lambda q: q["number"])
            page_path = render_page(page_number, temp)
            page = Image.open(page_path).convert("RGB")
            if page_number == 6:
                starts = [MANUAL_PAGE_6[q["number"]] for q in questions]
            elif page_number == 19:
                starts = [MANUAL_PAGE_19[q["number"]] for q in questions]
            else:
                starts = marker_starts(page, len(questions), questions[0]["number"])
                if not starts or len(starts) != len(questions):
                    raise RuntimeError(f"Could not find all question starts on page {page_number}: {starts}")
            for index, question in enumerate(questions):
                if question["number"] not in targets:
                    continue
                # The target is centered between its adjacent questions where possible.
                top = starts[index - 1] - 25 if index else max(0, starts[index] - 110)
                bottom = starts[index + 2] - 12 if index + 2 < len(starts) else page.height
                top = max(0, top)
                if bottom - top < 420:
                    bottom = min(page.height, top + 700)
                crop = page.crop((0, top, page.width, bottom))
                target = ROOT / question["image"]
                temporary = target.with_suffix(".tmp.png")
                crop.save(temporary, "PNG", optimize=True)
                temporary.replace(target)
                print(question["number"], page_number, (top, bottom), crop.size)


if __name__ == "__main__":
    main()
