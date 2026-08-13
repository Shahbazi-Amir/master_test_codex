import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "computer_questions": ROOT / "assets/source/arshad_computer_1405.pdf",
    "computer_key": ROOT / "assets/source/answer_key_computer_1405.pdf",
    "electrical_key": ROOT / "assets/source/answer_key_electrical_1405.pdf",
}
OUT = ROOT / "data/diagnostics/1405_new_sources"


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, errors="replace")


def page_count(pdf: Path) -> int:
    info = run("pdfinfo", str(pdf))
    match = re.search(r"^Pages:\s+(\d+)", info, re.M)
    if not match:
        raise RuntimeError(f"Could not determine page count for {pdf}")
    return int(match.group(1))


def extract_page_text(pdf: Path, page: int, work: Path) -> tuple[str, str]:
    native = work / f"native-{page}.txt"
    subprocess.run([
        "pdftotext", "-f", str(page), "-l", str(page), "-layout",
        str(pdf), str(native),
    ], check=True)
    text = native.read_text(encoding="utf-8", errors="replace").strip()
    if len(re.sub(r"\s+", "", text)) >= 80:
        return text, "pdftotext"

    prefix = work / f"render-{page}"
    subprocess.run([
        "pdftoppm", "-f", str(page), "-l", str(page), "-r", "220", "-png",
        str(pdf), str(prefix),
    ], check=True)
    images = sorted(work.glob(f"render-{page}-*.png"))
    if not images:
        images = sorted(work.glob(f"render-{page}.png"))
    if not images:
        raise RuntimeError(f"No rendered image for {pdf} page {page}")
    image = images[0]
    ocr_base = work / f"ocr-{page}"
    subprocess.run([
        "tesseract", str(image), str(ocr_base), "-l", "fas+eng", "--psm", "6"
    ], check=True)
    return ocr_base.with_suffix(".txt").read_text(encoding="utf-8", errors="replace").strip(), "ocr_fas_eng"


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
            prefix = target / f"page-{page:02d}"
            subprocess.run([
                "pdftoppm", "-f", str(page), "-l", str(page), "-r", "150", "-png",
                str(pdf), str(prefix),
            ], check=True)
            generated = sorted(target.glob(f"page-{page:02d}-*.png"))
            if generated:
                generated[0].rename(target / f"page-{page:02d}.png")

    return {
        "name": name,
        "path": str(pdf.relative_to(ROOT)),
        "size_bytes": pdf.stat().st_size,
        "page_count": count,
        "pages": pages,
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
