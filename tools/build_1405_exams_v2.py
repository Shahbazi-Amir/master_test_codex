#!/usr/bin/env python3
"""Run the 1405 builder with fixed-coordinate official-key cell extraction."""

import csv
import io
import json
import re
import subprocess
import tempfile
import traceback
from pathlib import Path

from PIL import Image, ImageOps

import build_1405_exams as base

DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize(value: str) -> str:
    return value.translate(DIGITS).replace("|", "1")


def cluster(values: list[float], tolerance: float = 35) -> list[list[float]]:
    groups: list[list[float]] = []
    for value in sorted(values):
        if not groups or abs(value - sum(groups[-1]) / len(groups[-1])) > tolerance:
            groups.append([value])
        else:
            groups[-1].append(value)
    return groups


def fixed_parse_key_table(pdf: Path, groups: list[tuple[int, int]], temp: Path, label: str) -> list[int]:
    # The computer key was transcribed row-by-row from the official table and is
    # checked against the diagnostic OCR. This avoids Persian digit 1 being lost
    # when it is printed as a thin vertical stroke.
    if label == "computer":
        answers = list(base.COMPUTER_KEY_MANUAL)
        (base.DIAG / "parsed_computer_key_cells.json").write_text(
            json.dumps([
                {"question": number, "answer": answer, "source": "verified_official_table"}
                for number, answer in enumerate(answers, 1)
            ], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return answers

    image_path = base.render_key(pdf, temp / f"{label}-fixed-key.png")
    tsv = subprocess.check_output([
        "tesseract", str(image_path), "stdout", "-l", "fas+eng", "--psm", "6", "tsv"
    ], text=True, errors="replace")
    answer_x = [550, 890, 1225, 1565][:len(groups)]
    tokens = []
    for row in csv.DictReader(io.StringIO(tsv), delimiter="\t"):
        raw = row.get("text", "").strip()
        if row.get("level") != "5" or not raw:
            continue
        digits = re.sub(r"\D", "", normalize(raw))
        if not digits or digits[-1] not in "1234":
            continue
        x = int(row["left"]) + int(row["width"]) / 2
        y = int(row["top"]) + int(row["height"]) / 2
        nearest = min(range(len(answer_x)), key=lambda index: abs(x - answer_x[index]))
        if abs(x - answer_x[nearest]) <= 85 and 550 <= y <= 4600:
            tokens.append({
                "answer": int(digits[-1]),
                "x": x,
                "y": y,
                "column": nearest,
                "confidence": float(row["conf"]),
                "raw": raw,
            })

    y_groups = cluster([token["y"] for token in tokens])
    centers = [sum(values) / len(values) for values in y_groups if len(values) >= max(1, len(groups) - 1)]
    if len(centers) > 40:
        best = None
        for start in range(len(centers) - 39):
            window = centers[start:start + 40]
            gaps = [window[i + 1] - window[i] for i in range(39)]
            score = (max(gaps) - min(gaps)) + abs(sum(gaps) / len(gaps) - 98)
            if best is None or score < best[0]:
                best = (score, window)
        centers = best[1]
    if len(centers) < 38:
        raise RuntimeError(f"Only {len(centers)} answer rows found for {label}")
    if len(centers) != 40:
        first, last = centers[0], centers[-1]
        centers = [first + (last - first) * index / 39 for index in range(40)]

    image = Image.open(image_path).convert("L")
    spacing = sum(centers[index + 1] - centers[index] for index in range(39)) / 39

    def read_cell(row_index: int, column: int) -> int:
        y = centers[row_index]
        candidates = [
            token for token in tokens
            if token["column"] == column and abs(token["y"] - y) <= max(38, spacing * 0.42)
        ]
        if candidates:
            return max(candidates, key=lambda token: token["confidence"])["answer"]

        x = answer_x[column]
        crop = image.crop((int(x - 75), int(y - spacing * 0.42), int(x + 75), int(y + spacing * 0.42)))
        crop = ImageOps.autocontrast(crop.resize((crop.width * 5, crop.height * 5)))
        attempts = []
        for threshold in (105, 130, 155, 180, 205, 225):
            binary = crop.point(lambda pixel, limit=threshold: 255 if pixel > limit else 0)
            with tempfile.NamedTemporaryFile(suffix=".png") as handle:
                binary.save(handle.name)
                text = subprocess.check_output([
                    "tesseract", handle.name, "stdout", "--psm", "10",
                    "-c", "tessedit_char_whitelist=1234۱۲۳۴١٢٣٤"
                ], text=True, errors="replace")
            digits = re.sub(r"\D", "", normalize(text))
            if digits and digits[-1] in "1234":
                attempts.append(int(digits[-1]))
        if not attempts:
            diagnostic = base.DIAG / "failed_key_cells" / f"{label}-row-{row_index + 1:02d}-column-{column + 1}.png"
            diagnostic.parent.mkdir(parents=True, exist_ok=True)
            crop.save(diagnostic)
            raise RuntimeError(f"Unreadable {label} key cell row {row_index + 1}, column {column + 1}")
        return max(set(attempts), key=attempts.count)

    answers = [None] * max(end for _, end in groups)
    detail = []
    for column, (start, end) in enumerate(groups):
        for row_index, question in enumerate(range(start, end + 1)):
            answer = read_cell(row_index, column)
            answers[question - 1] = answer
            detail.append({"question": question, "answer": answer, "row": row_index + 1, "column": column + 1})
    if any(answer not in {1, 2, 3, 4} for answer in answers):
        raise RuntimeError(f"Incomplete parsed {label} key")
    (base.DIAG / f"parsed_{label}_key_cells.json").write_text(
        json.dumps(detail, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return answers


def main() -> None:
    base.parse_key_table = fixed_parse_key_table
    base.DIAG.mkdir(parents=True, exist_ok=True)
    try:
        summary = base.build()
        payload = {"success": True, "parser": "fixed_answer_cells", "summary": summary}
    except Exception:
        payload = {"success": False, "parser": "fixed_answer_cells", "error": traceback.format_exc()}
    base.STATUS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    if not payload["success"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
