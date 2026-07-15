#!/usr/bin/env python3
"""Rebuild selected question images from the official 1404 PDF with safe margins."""

import argparse
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

MANUAL_STARTS = {
    41: (10, 215), 42: (10, 700),
    43: (11, 155), 44: (11, 535), 45: (11, 945), 46: (11, 1235),
    47: (12, 160), 48: (12, 455), 49: (12, 695), 50: (12, 1135),
    51: (13, 150), 52: (13, 940),
    53: (14, 148), 54: (14, 897), 55: (14, 1261),
    56: (15, 175), 57: (15, 615), 58: (15, 1115),
    59: (16, 165), 60: (16, 570), 61: (16, 1030),
    62: (17, 160), 63: (17, 650), 64: (17, 1120),
    65: (18, 150), 66: (18, 485), 67: (18, 1040),
    68: (19, 145), 69: (19, 1030),
    70: (20, 145),
}

MANUAL_ENDS = {70: 930}


def render_pages(directory, first=6, last=34):
    pages = {}
    for number in range(first, last + 1):
        prefix = directory / f"page_{number}"
        subprocess.run(
            ["pdftoppm", "-f", str(number), "-l", str(number), "-r", "150",
             "-png", "-singlefile", str(PDF), str(prefix)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        path = prefix.with_suffix(".png")
        pages[number] = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    return pages


def locate(template, pages, expected_page):
    best = None
    # Old source_page values can straddle a page boundary, so search nearby.
    candidates = range(max(6, expected_page - 2), min(34, expected_page + 2) + 1)
    for page_number in candidates:
        page = pages[page_number]
        if template.shape[0] > page.shape[0] or template.shape[1] > page.shape[1]:
            continue
        result = cv2.matchTemplate(page, template, cv2.TM_CCOEFF_NORMED)
        _, score, _, point = cv2.minMaxLoc(result)
        candidate = (score, page_number, point[1], template.shape[0])
        if best is None or candidate > best:
            best = candidate
    if best is None or best[0] < .52:
        raise RuntimeError(f"Could not locate crop near page {expected_page}; best={best}")
    return best


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("first", type=int)
    parser.add_argument("last", type=int)
    args = parser.parse_args()

    data = json.loads(DATA.read_text(encoding="utf-8"))
    questions = [q for q in data["questions"] if args.first <= q["number"] <= args.last and q.get("image")]
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        pages = render_pages(temp)
        located = defaultdict(list)
        for question in questions:
            template = cv2.imread(str(ROOT / question["image"]), cv2.IMREAD_GRAYSCALE)
            if template is None:
                raise RuntimeError(f"Unreadable image for question {question['number']}")
            if question["number"] in MANUAL_STARTS:
                page_number, top = MANUAL_STARTS[question["number"]]
                score, height = 1.0, template.shape[0]
            else:
                score, page_number, top, height = locate(template, pages, question["source_page"])
            located[page_number].append((top, question, score, height))

        for page_number, entries in located.items():
            entries.sort(key=lambda item: item[0])
            page_path = temp / f"page_{page_number}.png"
            page = Image.open(page_path).convert("RGB")
            for index, (matched_top, question, score, old_height) in enumerate(entries):
                top = max(0, matched_top - 34)
                if index + 1 < len(entries):
                    bottom = max(top + 180, entries[index + 1][0] - 8)
                else:
                    bottom = MANUAL_ENDS.get(
                        question["number"],
                        min(page.height, matched_top + old_height + 60),
                    )
                crop = page.crop((0, top, page.width, bottom))
                target = ROOT / question["image"]
                temporary = target.with_suffix(".tmp.png")
                crop.save(temporary, "PNG", optimize=True)
                temporary.replace(target)
                question["source_page"] = page_number
                print(question["number"], page_number, matched_top, f"{score:.3f}", crop.size)

    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
