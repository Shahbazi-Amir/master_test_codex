import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PDF = ROOT.parent / "arshad_bargh_1404_1251.pdf"
RENDERED_PAGES = ROOT / "work" / "cleanpages"
PDF_TARGET = ROOT / "assets" / "source" / "arshad_bargh_1404_1251.pdf"
QUESTIONS_DIR = ROOT / "assets" / "questions" / "1404"
DATA_TARGET = ROOT / "data" / "questions" / "exam_1404.json"
KEY_TARGET = ROOT / "data" / "answer_keys" / "key_1404.json"


ANSWERS = [
    2, 1, 4, 3, 1, 3, 4, 2, 1, 2, 3, 4, 2, 1, 3, 4, 1, 2, 3, 4,
    2, 1, 4, 2, 1, 1, 4, 2, 3, 3, 4, 2, 2, 1, 3, 1, 2, 1, 4, 3,
    2, 4, 3, 3, 2, 1, 4, 3, 1, 2, 1, 4, 1, 2, 1, 2, 1, 4, 2, 3,
    3, 3, 1, 2, 2, 1, 2, 4, 2, 3, 2, 1, 4, 3, 2, 1, 3, 3, 2, 2,
    2, 3, 4, 2, 1, 4, 2, 3, 1, 3, 2, 1, 1, 2, 3, 2, 4, 1, 3, 1,
    3, 4, 3, 1, 3, 3, 4, 2, 1, 4, 2, 1, 3, 3, 4, 4, 3, 2, 1, 4,
    3, 2, 2, 3, 1,
]


PAGE_RANGES = [
    (1, 7, 2), (8, 14, 3), (15, 18, 4), (19, 21, 5),
    (22, 27, 6), (28, 31, 7), (32, 36, 8), (37, 40, 9),
    (41, 43, 10), (44, 47, 11), (48, 50, 12), (51, 52, 13),
    (53, 55, 14), (56, 59, 15), (60, 62, 16), (63, 64, 17),
    (65, 67, 18), (68, 69, 19), (70, 71, 20), (72, 76, 21),
    (77, 80, 22), (81, 84, 23), (85, 87, 24), (88, 90, 25),
    (91, 91, 26), (92, 95, 27), (96, 98, 28), (99, 102, 29),
    (103, 107, 30), (108, 110, 31), (111, 113, 32),
    (114, 118, 33), (119, 125, 34),
]


SUBJECT_RANGES = [
    (1, 25, "زبان عمومی و تخصصی (انگلیسی)"),
    (26, 40, "ریاضیات"),
    (41, 55, "مدارهای الکتریکی ۱ و ۲"),
    (56, 70, "الکترونیک ۱ و ۲ و سیستم‌های دیجیتال ۱"),
    (71, 85, "ماشین‌های الکتریکی ۱ و ۲ و تحلیل سیستم‌های انرژی الکتریکی ۱"),
    (86, 95, "سیستم‌های کنترل خطی"),
    (96, 105, "سیگنال‌ها و سیستم‌ها"),
    (106, 115, "الکترومغناطیس"),
    (116, 125, "مقدمه‌ای بر مهندسی زیست‌پزشکی"),
]


def source_page(question_number: int) -> int:
    for start, end, page in PAGE_RANGES:
        if start <= question_number <= end:
            return page
    raise ValueError(f"No source page for question {question_number}")


def subject(question_number: int) -> str:
    for start, end, title in SUBJECT_RANGES:
        if start <= question_number <= end:
            return title
    raise ValueError(f"No subject for question {question_number}")


def main() -> None:
    if len(ANSWERS) != 125 or any(answer not in {1, 2, 3, 4} for answer in ANSWERS):
        raise RuntimeError("The official answer key must contain 125 valid answers")

    PDF_TARGET.parent.mkdir(parents=True, exist_ok=True)
    QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_TARGET.parent.mkdir(parents=True, exist_ok=True)
    KEY_TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_PDF, PDF_TARGET)

    questions = []
    answers = []
    for number, correct_answer in enumerate(ANSWERS, start=1):
        page = source_page(number)
        image_name = f"question_{number:03d}.png"
        source_image = RENDERED_PAGES / f"page-{page:02d}.png"
        if not source_image.exists() or source_image.stat().st_size == 0:
            raise FileNotFoundError(source_image)
        shutil.copy2(source_image, QUESTIONS_DIR / image_name)
        lesson = subject(number)
        questions.append({
            "number": number,
            "subject": lesson,
            "image": f"assets/questions/1404/{image_name}",
            "source_page": page,
            "choices": [1, 2, 3, 4],
            "correct_answer": correct_answer,
            "explanation": None,
            "explanation_status": "pending_review",
            "explanation_sources": [],
        })
        answers.append({
            "question_number": number,
            "correct_option": correct_answer,
            "lesson": lesson,
        })

    exam = {
        "exam_code": "1251",
        "year": 1404,
        "title": "آزمون کارشناسی ارشد مهندسی برق ۱۴۰۴",
        "booklet_code": "535C",
        "total_questions": 125,
        "duration_minutes": 250,
        "source_pdf": "assets/source/arshad_bargh_1404_1251.pdf",
        "image_policy": "Each question has a lossless copy of its complete official source page to avoid cutting formulas, diagrams, passages, or choices.",
        "questions": questions,
    }
    key = {
        "exam_code": "1251",
        "year": 1404,
        "booklet_code": "535C",
        "total_questions": 125,
        "source": "Official answer-key page included in the source PDF",
        "source_pdf": "assets/source/arshad_bargh_1404_1251.pdf",
        "answers": answers,
    }
    DATA_TARGET.write_text(json.dumps(exam, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    KEY_TARGET.write_text(json.dumps(key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
