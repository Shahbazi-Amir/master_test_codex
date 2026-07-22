import csv
import io
import json
import re
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/diagnostics/1405_new_sources/key_tables"
KEYS = {
    "computer": ROOT / "assets/source/answer_key_computer_1405.pdf",
    "electrical": ROOT / "assets/source/answer_key_electrical_1405.pdf",
}
DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize(value: str) -> str:
    return value.translate(DIGITS).replace("|", "1").strip()


def render(pdf: Path, work: Path, name: str) -> Path:
    prefix = work / name
    subprocess.run([
        "pdftoppm", "-f", "1", "-l", "1", "-r", "400", "-gray", "-png",
        str(pdf), str(prefix),
    ], check=True)
    images = sorted(work.glob(f"{name}-*.png")) or sorted(work.glob(f"{name}.png"))
    if not images:
        raise RuntimeError(f"render failed: {pdf}")
    return images[0]


def scan(image: Path, psm: int) -> list[dict]:
    data = subprocess.check_output([
        "tesseract", str(image), "stdout", "-l", "fas+eng", "--psm", str(psm), "tsv"
    ], text=True, errors="replace")
    tokens = []
    for row in csv.DictReader(io.StringIO(data), delimiter="\t"):
        raw = row.get("text", "").strip()
        if row.get("level") != "5" or not raw:
            continue
        normalized = normalize(raw)
        numeric = re.sub(r"\D", "", normalized)
        tokens.append({
            "raw": raw,
            "normalized": normalized,
            "numeric": int(numeric) if numeric and len(numeric) <= 3 else None,
            "left": int(row["left"]),
            "top": int(row["top"]),
            "width": int(row["width"]),
            "height": int(row["height"]),
            "confidence": float(row["conf"]),
        })
    return tokens


def rows_from_tokens(tokens: list[dict], tolerance: int = 28) -> list[dict]:
    numeric = [token for token in tokens if token["numeric"] is not None]
    numeric.sort(key=lambda token: (token["top"] + token["height"] / 2, token["left"]))
    rows: list[list[dict]] = []
    centers: list[float] = []
    for token in numeric:
        center = token["top"] + token["height"] / 2
        index = next((i for i, old in enumerate(centers) if abs(old - center) <= tolerance), None)
        if index is None:
            rows.append([token])
            centers.append(center)
        else:
            rows[index].append(token)
            centers[index] = sum(item["top"] + item["height"] / 2 for item in rows[index]) / len(rows[index])
    result = []
    for center, row in sorted(zip(centers, rows), key=lambda item: item[0]):
        row.sort(key=lambda token: token["left"])
        result.append({"center_y": center, "values": row})
    return result


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="key-table-scan-") as temp:
        work = Path(temp)
        for name, pdf in KEYS.items():
            image = render(pdf, work, name)
            payload = {"name": name, "scans": {}}
            for psm in (3, 6, 11, 12):
                tokens = scan(image, psm)
                payload["scans"][str(psm)] = {
                    "tokens": tokens,
                    "rows": rows_from_tokens(tokens),
                }
            (OUT / f"{name}.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
    print("scanned key tables")


if __name__ == "__main__":
    main()
