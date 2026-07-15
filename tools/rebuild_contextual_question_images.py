#!/usr/bin/env python3
"""Rebuild 1404 image questions with the target surrounded by adjacent questions."""

import json
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

import cv2
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "assets/source/arshad_bargh_1404_1251.pdf"
DATA = ROOT / "data/questions/exam_1404.json"


def render_page(number, directory):
    prefix = directory / f"page_{number}"
    subprocess.run(
        ["pdftoppm", "-f", str(number), "-l", str(number), "-r", "150",
         "-png", "-singlefile", str(PDF), str(prefix)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return prefix.with_suffix(".png")


def locate(template, page):
    if template.shape[1] > page.shape[1]:
        template = template[:, :page.shape[1]]
    result = cv2.matchTemplate(page, template, cv2.TM_CCOEFF_NORMED)
    _, score, _, point = cv2.minMaxLoc(result)
    if score < .92:
        raise RuntimeError(f"Image match score is too low: {score:.3f}")
    return point[1], template.shape[0], score


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    questions = [q for q in data["questions"] if 26 <= q["number"] <= 125 and q.get("image")]
    by_page = defaultdict(list)
    for question in questions:
        by_page[question["source_page"]].append(question)

    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        for page_number, page_questions in sorted(by_page.items()):
            page_path = render_page(page_number, temp)
            page_gray = cv2.imread(str(page_path), cv2.IMREAD_GRAYSCALE)
            page_image = Image.open(page_path).convert("RGB")
            located = []
            for question in page_questions:
                template = cv2.imread(str(ROOT / question["image"]), cv2.IMREAD_GRAYSCALE)
                if template is None:
                    raise RuntimeError(f"Unreadable question image: {question['number']}")
                top, height, score = locate(template, page_gray)
                # Existing crops have 34px of leading context. Recover the
                # approximate printed question start for contextual framing.
                start = min(page_image.height - 1, top + 34)
                located.append((start, top, height, score, question))
            located.sort(key=lambda item: item[0])

            for index, (start, matched_top, old_height, score, question) in enumerate(located):
                # Include the previous question when available.
                top = located[index - 1][0] if index > 0 else max(0, start - 100)
                # Include the next question completely by ending at the start
                # of the question after it. At page edges retain the full page.
                if index + 2 < len(located):
                    bottom = located[index + 2][0] - 8
                else:
                    bottom = page_image.height
                if bottom - top < 360:
                    top = max(0, start - 180)
                    bottom = min(page_image.height, start + 620)
                crop = page_image.crop((0, top, page_image.width, bottom))
                target = ROOT / question["image"]
                temporary = target.with_suffix(".tmp.png")
                crop.save(temporary, "PNG", optimize=True)
                temporary.replace(target)
                print(question["number"], page_number, f"{score:.3f}", crop.size)


if __name__ == "__main__":
    main()
