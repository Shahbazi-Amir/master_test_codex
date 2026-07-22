import json
import re
import subprocess
import tempfile
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


def embedded_text(page: int) -> str:
    return run(
        "pdftotext",
        "-f", str(page),
        "-l", str(page),
        "-layout",
        "-enc", "UTF-8",
        str(PDF),
        "-",
    ).replace("\x0c", "").strip()


def ocr_page(page: int, work_dir: Path) -> str:
    prefix = work_dir / f"page-{page:02d}"
    subprocess.check_call([
        "pdftoppm",
        "-f", str(page),
        "-l", str(page),
        "-singlefile",
        "-r", "200",
        "-png",
        str(PDF),
        str(prefix),
    ])
    image = prefix.with_suffix(".png")
    try:
        return run(
            "tesseract",
            str(image),
            "stdout",
            "-l", "fas+eng",
            "--psm", "3",
            "preserve_interword_spaces=1",
        ).strip()
    finally:
        image.unlink(missing_ok=True)


def likely_question_numbers(text: str) -> list[int]:
    normalized = normalize_digits(text)
    numbers = []
    patterns = [
        r"^\s*(\d{1,3})(?:\s|[.)\-:])",
        r"(?:^|\s)(\d{1,3})\s*[-.)]\s*",
    ]
    for line in normalized.splitlines():
        for pattern in patterns:
            for match in re.finditer(pattern, line):
                value = int(match.group(1))
                if 1 <= value <= 200:
                    numbers.append(value)
    return sorted(set(numbers))


def main() -> None:
    if not PDF.exists() or PDF.stat().st_size == 0:
        raise FileNotFoundError(PDF)

    count = page_count()
    pages = []
    with tempfile.TemporaryDirectory(prefix="exam-1405-ocr-") as temp:
        work_dir = Path(temp)
        for page in range(1, count + 1):
            text = embedded_text(page)
            method = "embedded"
            if not text:
                text = ocr_page(page, work_dir)
                method = "ocr_fas_eng"
            pages.append({
                "page": page,
                "method": method,
                "text": text,
                "likely_question_numbers": likely_question_numbers(text),
            })
            print(f"Processed page {page}/{count}: {pages[-1]['likely_question_numbers']}")

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
