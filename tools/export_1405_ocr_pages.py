import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "diagnostics" / "exam_1405_pdf_analysis.json"
TARGET = ROOT / "data" / "diagnostics" / "ocr_pages"


def main() -> None:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    TARGET.mkdir(parents=True, exist_ok=True)
    for page in data["pages"]:
        number = page["page"]
        content = (
            f"PAGE: {number}\n"
            f"METHOD: {page.get('method', '')}\n"
            f"CANDIDATES: {page.get('likely_question_numbers', [])}\n"
            "\n"
            f"{page.get('text', '')}\n"
        )
        (TARGET / f"page-{number:02d}.txt").write_text(content, encoding="utf-8")
    print(f"Exported {len(data['pages'])} OCR page files")


if __name__ == "__main__":
    main()
