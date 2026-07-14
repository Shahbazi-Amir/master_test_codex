#!/usr/bin/env python3
"""Split repeated full-page question images into per-question vertical crops."""

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]


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


def choose_boundaries(image, count, first_number):
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
