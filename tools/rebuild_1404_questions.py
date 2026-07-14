#!/usr/bin/env python3
"""Rebuild 1404 question assets from the untouched source PDF.

The script intentionally refuses to guess missing question boundaries. Any page
that OCR cannot identify exactly must be added to MANUAL_STARTS after visual QA.
"""

import json
import re
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EXAM_PATH = ROOT / "data/questions/computer_engineering/exam_1404.json"
SOURCE_PDF = ROOT / "assets/source/computer_engineering/1404/questions.pdf"
RENDER_DIR = ROOT / "tmp/pdfs/1404/pages"
OUTPUT_DIR = ROOT / "assets/questions/computer_engineering/1404"
CONTEXT_DIR = ROOT / "assets/contexts/computer_engineering/1404"

# Populated only after comparing a rendered source page with OCR output.
# Format: PDF page number -> {question number: y coordinate at 150 dpi}.
MANUAL_STARTS = {
    6: {26: 1162, 27: 1371},
    7: {28: 224, 29: 556, 30: 774, 31: 1152},
    8: {32: 198, 33: 479, 34: 681, 35: 964, 36: 1249},
    9: {37: 194, 38: 479, 39: 783, 40: 1107},
    10: {41: 196, 42: 484, 43: 768, 44: 1131, 45: 1343},
    11: {46: 199, 47: 550, 48: 778, 49: 1067, 50: 1307},
    12: {51: 194, 52: 748, 53: 990, 54: 1197},
    13: {55: 194, 56: 475, 57: 827, 58: 1044, 59: 1211},
    14: {60: 194, 61: 350, 62: 768, 63: 1008, 64: 1295},
    15: {65: 194, 66: 773, 67: 1080},
    16: {68: 194, 69: 480, 70: 932, 71: 1190},
    17: {72: 196, 73: 520, 74: 1003},
    18: {75: 194, 76: 811, 77: 1009, 78: 1326},
    19: {79: 197, 80: 439, 81: 741, 82: 944, 83: 1228},
    20: {84: 197, 85: 599, 86: 1358},
    21: {87: 194, 88: 436, 89: 786, 90: 1140},
    22: {91: 196, 92: 606, 93: 918, 94: 1354},
    23: {95: 197, 96: 743, 97: 948, 98: 1106, 99: 1311, 100: 1472},
    24: {101: 196, 102: 315, 103: 560, 104: 841, 105: 1046, 106: 1164, 107: 1326},
    25: {108: 196, 109: 682, 110: 1000, 111: 1205, 112: 1407},
    26: {113: 197, 114: 396, 115: 538},
}

CONTEXT_CROPS = {
    "cloze_a": (2, 1490, 1745),
    "cloze_b": (3, 165, 345),
    "passage_1": (3, 650, 1415),
    "passage_2": (4, 710, 1660),
    "passage_3": (5, 640, 1660),
}

DIGIT_MAP = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def render_pages():
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    if len(list(RENDER_DIR.glob("page-*.png"))) >= 28:
        return
    subprocess.run([
        "pdftoppm", "-f", "1", "-l", "28", "-r", "150", "-png",
        str(SOURCE_PDF), str(RENDER_DIR / "page")
    ], check=True)


def tsv_words(page_path):
    result = subprocess.run([
        "tesseract", str(page_path), "stdout", "-l", "fas+eng", "--psm", "6",
        "-c", "tessedit_create_tsv=1"
    ], capture_output=True, text=True, check=True)
    words = []
    for row in result.stdout.splitlines()[1:]:
        columns = row.split("\t", 11)
        if len(columns) != 12 or columns[0] != "5":
            continue
        left, top, width, height = map(int, columns[6:10])
        words.append((left, top, width, height, columns[11].strip()))
    return words


def ocr_starts(page_path, expected):
    image = Image.open(page_path)
    found = {}
    for left, top, width, height, token in tsv_words(page_path):
        normalized = token.translate(DIGIT_MAP)
        match = re.search(r"\d+", normalized)
        has_dash = any(mark in token for mark in ("-", "–", "—"))
        if not (match and has_dash and len(token) <= 9):
            continue
        number = int(match.group())
        in_margin = (left < image.width * .14) if number <= 25 else (left + width > image.width * .84)
        if not in_margin:
            continue
        if number in expected:
            found.setdefault(number, top)
    found.update(MANUAL_STARTS.get(int(page_path.stem.split("-")[-1]), {}))
    return found


def main():
    render_pages()
    exam = json.loads(EXAM_PATH.read_text(encoding="utf-8"))
    pages = defaultdict(list)
    for question in exam["questions"]:
        pages[int(question["source_page"])].append(question)

    unresolved = []
    for pdf_page, questions in sorted(pages.items()):
        questions.sort(key=lambda item: item["number"])
        page_path = RENDER_DIR / f"page-{pdf_page:02}.png"
        expected = [item["number"] for item in questions]
        starts = ocr_starts(page_path, set(expected))
        missing = [number for number in expected if number not in starts]
        if missing:
            unresolved.append((pdf_page, expected, missing, starts))
            continue
        image = Image.open(page_path).convert("RGB")
        ordered = [starts[number] for number in expected]
        for index, question in enumerate(questions):
            # Keep generous vertical overlap around every question.  A small
            # amount of neighbouring whitespace is preferable to clipping a
            # formula, option or the final line of a question.
            top = max(0, ordered[index] - 42)
            bottom = ordered[index + 1] + 8 if index + 1 < len(ordered) else image.height - 10
            if bottom <= top + 35:
                raise RuntimeError(f"Invalid crop for question {question['number']} on page {pdf_page}")
            crop = image.crop((8, top, image.width - 8, min(image.height, bottom)))
            crop.save(OUTPUT_DIR / f"question_{question['number']:03}.png")

    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    for name, (pdf_page, top, bottom) in CONTEXT_CROPS.items():
        page = Image.open(RENDER_DIR / f"page-{pdf_page:02}.png").convert("RGB")
        page.crop((25, top, page.width - 25, bottom)).save(CONTEXT_DIR / f"{name}.png")

    context_groups = {
        range(8, 11): ["cloze_a", "cloze_b"],
        range(11, 16): ["passage_1"],
        range(16, 21): ["passage_2"],
        range(21, 26): ["passage_3"],
    }
    for question in exam["questions"]:
        for numbers, names in context_groups.items():
            if question["number"] in numbers:
                if question.get("context"):
                    question.pop("context_images", None)
                else:
                    question["context_images"] = [
                        f"assets/contexts/computer_engineering/1404/{name}.png" for name in names
                    ]
                break
        else:
            question.pop("context_images", None)
    EXAM_PATH.write_text(json.dumps(exam, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if unresolved:
        for item in unresolved:
            print(f"page={item[0]} expected={item[1]} missing={item[2]} found={item[3]}")
        raise SystemExit(f"Refusing to guess boundaries on {len(unresolved)} pages")


if __name__ == "__main__":
    main()
