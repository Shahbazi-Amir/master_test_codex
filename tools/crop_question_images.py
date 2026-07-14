#!/usr/bin/env python3
"""Split repeated full-page question images into per-question vertical crops."""

import json
import os
import re
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(os.environ.get("EXAM_ROOT", Path(__file__).resolve().parents[1])).resolve()


def ocr_starts(image, count, first_number):
    """Locate printed ``NN-`` question labels with Persian/English OCR."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".png") as source:
            image.save(source.name)
            result = subprocess.run(
                ["tesseract", source.name, "stdout", "-l", "fas+eng", "--psm", "6",
                 "-c", "tessedit_create_tsv=1"],
                capture_output=True, text=True, check=True,
            )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    expected = set(range(first_number, first_number + count))
    digit_map = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    candidates = {}
    for line in result.stdout.splitlines()[1:]:
        columns = line.split("\t", 11)
        if len(columns) != 12 or columns[0] != "5":
            continue
        left, top, width, height = map(int, columns[6:10])
        token = columns[11].strip()
        in_margin = left < image.width * .20 or left + width > image.width * .78
        normalized = token.translate(digit_map)
        match = re.search(r"\d+", normalized)
        is_label = any(mark in token for mark in ("-", "–", "—")) and len(token) <= 8
        if in_margin and is_label and match and top > image.height * .085:
            number = int(match.group())
            if number in expected:
                candidates.setdefault(number, top + height // 2)
    return [candidates[number] for number in sorted(expected)] if set(candidates) == expected else None


def blank_gaps(image):
    gray = np.asarray(ImageOps.grayscale(image))
    ink = gray < 238
    margin = max(20, image.width // 30)
    counts = ink[:, margin:-margin].sum(axis=1)
    threshold = max(3, int(image.width * 0.004))
    blank = counts <= threshold
    gaps, start = [], None
    for y, value in enumerate(blank):
        if value and start is None: start = y
        if not value and start is not None:
            if y - start >= 5: gaps.append((start, y - 1))
            start = None
    return gaps, counts


def marker_starts(image, count, first_number):
    gray = np.asarray(ImageOps.grayscale(image))
    ink = gray < 205
    # The booklet prints English question numbers in the left margin and all
    # later (RTL) question numbers in the far-right margin.  Keeping these
    # bands narrow avoids mistaking option numbers and formulas for questions.
    band_ranges = (
        ((.035, .095), (.05, .11), (.065, .125)),
        ((.80, .86), (.83, .89), (.86, .92)),
    )
    choices = []
    preferred_band = 0 if first_number <= 30 else 1
    partial = {0: [], 1: []}
    for side, ranges in enumerate(band_ranges):
      for low, high in ranges:
        band = ink[:, int(image.width * low):int(image.width * high)]
        counts = band.sum(axis=1)
        mask = counts > 1
        groups, start = [], None
        for y, value in enumerate(mask):
            if value and start is None: start = y
            if not value and start is not None:
                height = y - start
                maximum = int(counts[start:y].max())
                total = int(counts[start:y].sum())
                center = (start + y - 1) // 2
                if 2 <= height <= 34 and 3 <= maximum <= 34 and total >= 28 and center > image.height * .095:
                    groups.append((center, total))
                start = None
        filtered = []
        for center, score in groups:
            if filtered and center - filtered[-1][0] < 24:
                # A question number can split into two small row clusters.
                previous_center, previous_score = filtered[-1]
                combined = previous_score + score
                merged_center = round((previous_center * previous_score + center * score) / combined)
                filtered[-1] = (merged_center, combined)
            else:
                filtered.append((center, score))
        if first_number == 1:
            filtered = [item for item in filtered if item[0] > image.height * .35]
        if len(filtered) > len(partial[side]):
            partial[side] = filtered
        if len(filtered) >= count:
            # Markers appear in page order.  Trailing passage text on English
            # pages can enter the margin, so take the first expected markers.
            selected = filtered[:count]
            choices.append((side != preferred_band, len(filtered) - count, [center for center, _ in selected]))
    if choices:
        return min(choices)[2]
    # A page can end the English section and start the RTL section.  In that
    # case question markers legitimately occur in both margins.
    combined = sorted(partial[0] + partial[1])
    merged = []
    for center, score in combined:
        if merged and center - merged[-1][0] < 18:
            if score > merged[-1][1]:
                merged[-1] = (center, score)
        else:
            merged.append((center, score))
    return [center for center, _ in merged[:count]] if len(merged) >= count else None


def choose_boundaries(image, count, first_number):
    starts = ocr_starts(image, count, first_number) or marker_starts(image, count, first_number)
    if starts:
        top = int(image.height * .29) if first_number == 1 else max(int(image.height * .04), starts[0] - 24)
        boundaries = [top]
        boundaries.extend(max(top + 80, start - 20) for start in starts[1:])
        boundaries.append(image.height)
        return boundaries
    if count == 1:
        return [max(0, int(image.height * .045)), image.height]
    gaps, counts = blank_gaps(image)
    top = max(0, int(image.height * .045))
    if first_number == 1:
        top = int(image.height * .29)
    opening_gaps = [] if first_number == 1 else [(end - start, end) for start, end in gaps if start > top and end < image.height * .58]
    if opening_gaps:
        width, end = max(opening_gaps)
        if width >= image.height * .055:
            top = end + 8
    nonblank = np.flatnonzero(counts > max(3, int(image.width * .004)))
    bottom = min(image.height, (int(nonblank[-1]) + 30) if len(nonblank) else image.height)
    span = bottom - top
    boundaries = [top]
    for index in range(1, count):
        if first_number == 1:
            first_end = int(image.height * .45)
            if index == 1:
                boundaries.append(first_end)
                continue
            target = first_end if index == 1 else first_end + (bottom - first_end) * (index - 1) / (count - 1)
            window = (bottom - first_end) / (count - 1) * .62
        else:
            target = top + span * index / count
            window = span / count * .68
        candidates = []
        for start, end in gaps:
            center = (start + end) / 2
            if boundaries[-1] + 45 < center < bottom - 45 and abs(center - target) <= window:
                width = end - start + 1
                score = width * 3 - abs(center - target) * .20
                candidates.append((score, int(center)))
        boundary = max(candidates)[1] if candidates else int(target)
        boundaries.append(boundary)
    boundaries.append(bottom)
    return boundaries


def crop_exam(path):
    exam = json.loads(path.read_text(encoding="utf-8"))
    by_page = defaultdict(list)
    for question in exam["questions"]:
        by_page[question["source_page"]].append(question)
    for questions in by_page.values():
        questions.sort(key=lambda item: item["number"])
        source = ROOT / questions[0]["image"]
        page = Image.open(source).convert("RGB")
        boundaries = choose_boundaries(page, len(questions), questions[0]["number"])
        pad_x = max(12, page.width // 80)
        for index, question in enumerate(questions):
            top = max(0, boundaries[index] - 12)
            bottom = min(page.height, boundaries[index + 1] + 12)
            if bottom - top < 180:
                center = (top + bottom) // 2
                top = max(0, center - 90)
                bottom = min(page.height, top + 180)
                top = max(0, bottom - 180)
            crop = page.crop((pad_x, top, page.width - pad_x, bottom))
            target = ROOT / question["image"]
            temporary = target.with_suffix(".tmp.png")
            crop.save(temporary, "PNG", optimize=True)
            temporary.replace(target)


def main():
    paths = sorted((ROOT / "data" / "questions").rglob("exam_*.json"))
    if not paths: raise SystemExit("No exam JSON files found")
    for path in paths: crop_exam(path)


if __name__ == "__main__":
    main()
