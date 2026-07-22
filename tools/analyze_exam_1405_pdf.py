import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "assets" / "source" / "arshad_bargh_1405_1251.pdf"
OUTPUT = ROOT / "data" / "diagnostics" / "exam_1405_pdf_analysis.json"


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, errors="replace")


def page_count() -> int:
    info = run("pdfinfo", str(PDF))
    match = re.search(r"^Pages:\s+(\d+)", info, flags=re.MULTILINE)
    if not match:
        raise RuntimeError("Could not determine PDF page count")
    return int(match.group(1))


def normalize_digits(text: str) -> str:
    table = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    return text.translate(table)


def extract_page(page: int) -> str:
    return run(
        "pdftotext",
        "-f", str(page),
        "-l", str(page),
        "-layout",
        "-enc", "UTF-8",
        str(PDF),
        "-",
    ).replace("\x0c", "").strip()


def likely_question_numbers(text: str) -> list[int]:
    normalized = normalize_digits(text)
    numbers = []
    for line in normalized.splitlines():
        stripped = line.strip()
        match = re.match(r"^(\d{1,3})(?:\s|[.)\-:])", stripped)
        if match:
            value = int(match.group(1))
            if 1 <= value <= 200:
                numbers.append(value)
    return sorted(set(numbers))


def main() -> None:
    if not PDF.exists() or PDF.stat().st_size == 0:
        raise FileNotFoundError(PDF)

    count = page_count()
    pages = []
    for page in range(1, count + 1):
        text = extract_page(page)
        pages.append({
            "page": page,
            "text": text,
            "likely_question_numbers": likely_question_numbers(text),
        })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps({
            "source_pdf": str(PDF.relative_to(ROOT)),
            "size_bytes": PDF.stat().st_size,
            "page_count": count,
            "pages": pages,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {count} pages")


if __name__ == "__main__":
    main()
