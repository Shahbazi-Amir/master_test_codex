import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "assets" / "source" / "arshad_bargh_1405_1251.pdf"
OUTPUT = ROOT / "data" / "diagnostics" / "marker_scans"
PAGES = range(28, 34)


def ocr(image: Path, psm: int) -> str:
    return subprocess.check_output([
        "tesseract", str(image), "stdout",
        "-l", "fas+eng", "--psm", str(psm),
        "preserve_interword_spaces=1",
    ], text=True, errors="replace").strip()


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="markers-1405-") as temp:
        temp_dir = Path(temp)
        for page in PAGES:
            prefix = temp_dir / f"page-{page:02d}"
            subprocess.check_call([
                "pdftoppm", "-f", str(page), "-l", str(page),
                "-singlefile", "-r", "300", "-png",
                str(PDF), str(prefix),
            ])
            source = prefix.with_suffix(".png")
            image = Image.open(source).convert("L")
            image = ImageOps.autocontrast(image)
            width, height = image.size
            regions = {
                "full": image,
                "left_35": image.crop((0, 0, int(width * 0.35), height)),
                "right_35": image.crop((int(width * 0.65), 0, width, height)),
            }
            chunks = [f"PAGE {page}", f"SIZE {width}x{height}"]
            for name, region in regions.items():
                path = temp_dir / f"page-{page:02d}-{name}.png"
                region.save(path)
                for psm in (6, 11, 12):
                    chunks.append(f"\n=== {name} / PSM {psm} ===\n{ocr(path, psm)}")
            (OUTPUT / f"page-{page:02d}.txt").write_text("\n".join(chunks) + "\n", encoding="utf-8")
            print(f"Scanned page {page}")


if __name__ == "__main__":
    main()
