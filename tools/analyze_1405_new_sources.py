import csv
import io
import json
import re
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "computer_questions": ROOT / "assets/source/arshad_computer_1405.pdf",
    "computer_key": ROOT / "assets/source/answer_key_computer_1405.pdf",
    "electrical_key": ROOT / "assets/source/answer_key_electrical_1405.pdf",
}
OUT = ROOT / "data/diagnostics/1405_new_sources"
DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹١٢٣٤٥٦٧٨٩", "01234567890123456789")


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, errors="replace")


def page_count(pdf: Path) -> int:
    info = run("pdfinfo", str(pdf))
    match = re.search(r"^Pages:\s+(\d+)", info, re.M)
    if not match:
        raise RuntimeError(f"Could not determine page count for {pdf}")
    return int(match.group(1))


def render_page(pdf: Path, page: int, work: Path, dpi: int = 220) -> Path:
    prefix = work / f"render-{page}-{dpi}"
    subprocess.run([
        "pdftoppm", "-f", str(page), "-l", str(page), "-r", str(dpi), "-png",
        str(pdf), str(prefix),
    ], check=True)
    images = sorted(work.glob(f"render-{page}-{dpi}-*.png")) or sorted(work.glob(f"render-{page}-{dpi}.png"))
    if not images:
        raise RuntimeError(f"No rendered image for {pdf} page {page}")
    return images[0]


def extract_page_text(pdf: Path, page: int, work: Path) -> tuple[str, str]:
    native = work / f"native-{page}.txt"
    subprocess.run([
        "pdftotext", "-f", str(page), "-l", str(page), "-layout",
        str(pdf), str(native),
    ], check=True)
    text = native.read_text(encoding="utf-8", errors="replace").strip()
    if len(re.sub(r"\s+", "", text)) >= 80:
        return text, "pdftotext"

    image = render_page(pdf, page, work)
    ocr_base = work / f"ocr-{page}"
    subprocess.run([
        "tesseract", str(image), str(ocr_base), "-l", "fas+eng", "--psm", "6"
    ], check=True)
    return ocr_base.with_suffix(".txt").read_text(encoding="utf-8", errors="replace").strip(), "ocr_fas_eng"


def normalize_digits(text: str) -> str:
    return text.translate(DIGITS).replace("–", "-").replace("—", "-")


def scan_question_markers(pdf: Path, count: int, target: Path, work: Path) -> list[dict]:
    reports = []
    for page in range(2, count + 1):
        image = render_page(pdf, page, work, 240)
        tsv = subprocess.check_output([
            "tesseract", str(image), "stdout", "-l", "fas+eng", "--psm", "6", "tsv"
        ], text=True, errors="replace")
        grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
        for row in csv.DictReader(io.StringIO(tsv), delimiter="\t"):
            if not row.get("text", "").strip() or row.get("level") != "5":
                continue
            grouped[(row["block_num"], row["par_num"], row["line_num"])].append(row)

        lines = []
        for words in grouped.values():
            words.sort(key=lambda item: int(item["left"]))
            text = " ".join(item["text"].strip() for item in words)
            normalized = normalize_digits(text)
            top = min(int(item["top"]) for item in words)
            left = min(int(item["left"]) for item in words)
            right = max(int(item["left"]) + int(item["width"]) for item in words)
            candidates = []
            for pattern in [r"(?:^|\s)(\d{1,3})\s*-", r"-\s*(\d{1,3})(?:\s|$)"]:
                candidates.extend(int(value) for value in re.findall(pattern, normalized))
            if candidates or "مجموعه دروس" in text or "ریاضیات" in text or "زبان عمومی" in text:
                lines.append({
                    "top": top,
                    "left": left,
                    "right": right,
                    "text": text,
                    "normalized": normalized,
                    "candidates": candidates,
                })
        lines.sort(key=lambda item: item["top"])
        report = {"page": page, "markers": lines}
        reports.append(report)
        (target / f"markers-page-{page:02d}.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return reports


def analyze(name: str, pdf: Path) -> dict:
    if not pdf.exists() or pdf.stat().st_size == 0:
        raise FileNotFoundError(pdf)
    count = page_count(pdf)
    target = OUT / name
    target.mkdir(parents=True, exist_ok=True)
    pages = []
    with tempfile.TemporaryDirectory(prefix=f"analyze-{name}-") as tmp:
        work = Path(tmp)
        for page in range(1, count + 1):
            text, method = extract_page_text(pdf, page, work)
            (target / f"page-{page:02d}.txt").write_text(
                f"PAGE: {page}\nMETHOD: {method}\n\n{text}\n",
                encoding="utf-8",
            )
            pages.append({"page": page, "method": method, "text": text})

        visual_pages = range(1, count + 1) if "key" in name else range(1, min(count, 4) + 1)
        for page in visual_pages:
            rendered = render_page(pdf, page, work, 150)
            rendered.replace(target / f"page-{page:02d}.png")

        markers = scan_question_markers(pdf, count, target, work) if name == "computer_questions" else []

    return {
        "name": name,
        "path": str(pdf.relative_to(ROOT)),
        "size_bytes": pdf.stat().st_size,
        "page_count": count,
        "pages": pages,
        "marker_pages": markers,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    results = {name: analyze(name, path) for name, path in SOURCES.items()}
    (OUT / "analysis.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({name: item["page_count"] for name, item in results.items()}))


if __name__ == "__main__":
    main()
