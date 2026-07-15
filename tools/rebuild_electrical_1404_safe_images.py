#!/usr/bin/env python3
"""Rebuild questions 26..125 from the original PDF with safe margins.

Question starts are detected from the short dash printed beside each Persian
question number.  This avoids relying on the old page map, which was off by
one on several pages.  Crops deliberately overlap a little vertically: a few
pixels of neighbouring whitespace are preferable to a clipped option or
formula.
"""

import json
import shutil
import subprocess
import tempfile
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "assets/source/arshad_bargh_1404_1251.pdf"
EXAM_PATH = ROOT / "data/questions/exam_1404.json"
OUTPUT = ROOT / "assets/questions/1404"
FIRST_PDF_PAGE = 6
LAST_PDF_PAGE = 34


def components(mask):
    """Return 8-connected component bounding boxes in a small boolean mask."""
    height, width = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    result = []
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]:
            continue
        queue = deque([(y, x)])
        seen[y, x] = True
        points = []
        while queue:
            cy, cx = queue.popleft()
            points.append((cy, cx))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < height and 0 <= nx < width and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
        ys = [point[0] for point in points]
        xs = [point[1] for point in points]
        result.append((min(xs), min(ys), max(xs) + 1, max(ys) + 1, len(points)))
    return result


def question_starts(image):
    gray = np.asarray(image.convert("L"))
    # Coordinates are for the fixed 150-dpi render below.  The printed dash
    # sits in this narrow far-right strip on every technical-question page.
    left, right = 1040, 1120
    region = gray[:, left:right] < 165
    candidates = []
    for x0, y0, x1, y1, area in components(region):
        global_x = x0 + left
        width, height = x1 - x0, y1 - y0
        if (
            1065 <= global_x <= 1100
            and y0 > 160
            and 7 <= width <= 16
            and 1 <= height <= 5
            and width / height >= 2
            and area >= 6
        ):
            candidates.append(y0)
    starts = []
    for y in sorted(candidates):
        if not starts or y - starts[-1] > 12:
            starts.append(y)
    return starts


def content_bottom(image, start):
    gray = np.asarray(image.convert("L"))
    ink_rows = np.flatnonzero((gray[:, 45:-45] < 242).sum(axis=1) > 5)
    later = ink_rows[ink_rows >= start]
    return min(image.height - 8, int(later[-1]) + 30) if len(later) else image.height - 8


def main():
    if not PDF.exists():
        raise FileNotFoundError(PDF)
    exam = json.loads(EXAM_PATH.read_text(encoding="utf-8"))
    technical = [question for question in exam["questions"] if question["number"] >= 26]
    with tempfile.TemporaryDirectory(prefix="electrical-1404-") as directory:
        prefix = Path(directory) / "page"
        subprocess.run(
            [
                "pdftoppm", "-f", str(FIRST_PDF_PAGE), "-l", str(LAST_PDF_PAGE),
                "-r", "150", "-png", str(PDF), str(prefix),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        detected = []
        for pdf_page in range(FIRST_PDF_PAGE, LAST_PDF_PAGE + 1):
            page_path = Path(directory) / f"page-{pdf_page:02d}.png"
            image = Image.open(page_path).convert("RGB")
            for start in question_starts(image):
                detected.append((pdf_page, start, page_path))

        if len(detected) != len(technical):
            raise RuntimeError(f"Detected {len(detected)} technical questions; expected {len(technical)}")

        for index, (question, (pdf_page, start, page_path)) in enumerate(zip(technical, detected)):
            image = Image.open(page_path).convert("RGB")
            next_item = detected[index + 1] if index + 1 < len(detected) else None
            if next_item and next_item[0] == pdf_page:
                bottom = next_item[1] + 18
            else:
                bottom = content_bottom(image, start)
            top = max(0, start - 40)
            bottom = min(image.height, max(top + 180, bottom))
            crop = image.crop((45, top, image.width - 45, bottom))
            filename = f"question_{question['number']:03}.webp"
            crop.save(OUTPUT / filename, "WEBP", quality=86, method=6)
            question["image"] = f"assets/questions/1404/{filename}"
            question["source_page"] = pdf_page

    # Text-first English questions do not need duplicated raster assets or
    # stale image references in the data file.
    for question in exam["questions"]:
        if question["number"] <= 25:
            question.pop("image", None)
    for number in range(1, 126):
        (OUTPUT / f"question_{number:03}.png").unlink(missing_ok=True)
    exam["image_policy"] = (
        "Questions 1-25 use reviewed text. Questions 26-125 use optimized WebP "
        "crops rebuilt from the official PDF with safe overlapping margins."
    )
    EXAM_PATH.write_text(json.dumps(exam, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
