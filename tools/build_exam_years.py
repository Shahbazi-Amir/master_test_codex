import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT_ROOT = Path("/tmp/exams")


EXAMS = {
    1403: {
        "pdf": INPUT_ROOT / "1403.pdf",
        "pages": INPUT_ROOT / "final1403",
        "booklet_code": "170C",
        "duration_minutes": 250,
        "answers": [
            2, 4, 1, 3, 3, 4, 1, 2, 2, 1, 1, 3, 2, 2, 3, 2, 4, 3, 1, 2,
            1, 4, 4, 3, 2, 4, 3, 1, 2, 3, 2, 1, 1, 2, 2, 1, 2, 3, 3, 4,
            2, 3, 4, 3, 1, 2, 2, 1, 4, 3, 1, 3, 4, 1, 2, 4, 2, 1, 1, 4,
            3, 2, 2, 2, 1, 3, 2, 4, 3, 2, 2, 1, 1, 4, 1, 4, 1, 3, 3, 3,
            4, 1, 3, 2, 3, 4, 2, 3, 1, 3, 1, 3, 2, 4, 2, 1, 4, 1, 2, 4,
            3, 3, 3, 2, 1, 4, 3, 1, 4, 1, 2, 4, 3, 2, 1, 3, 4, 1, 3, 2,
            1, 2, 1, 3, 4, 3, 1, 3, 4, 1, 4,
        ],
        "page_ranges": [
            (1, 7, 2), (8, 13, 3), (14, 20, 4), (21, 24, 5), (25, 29, 6),
            (30, 33, 7), (34, 37, 8), (38, 42, 9), (43, 46, 10), (47, 50, 11),
            (51, 54, 12), (55, 56, 13), (57, 60, 14), (61, 64, 15), (65, 65, 16),
            (66, 67, 17), (68, 70, 18), (71, 73, 19), (74, 79, 20), (80, 83, 21),
            (84, 87, 22), (88, 90, 23), (91, 92, 24), (93, 93, 25), (94, 97, 26),
            (98, 100, 27), (101, 105, 28), (106, 109, 29), (110, 113, 30),
            (114, 116, 31), (117, 119, 32), (120, 125, 33), (126, 131, 34),
        ],
        "subject_ranges": [
            (1, 25, "زبان عمومی و تخصصی (انگلیسی)"),
            (26, 40, "ریاضیات"),
            (41, 55, "مدارهای الکتریکی ۱ و ۲"),
            (56, 70, "الکترونیک ۱ و ۲ و سیستم‌های دیجیتال ۱"),
            (71, 85, "ماشین‌های الکتریکی ۱ و ۲ و تحلیل سیستم‌های انرژی الکتریکی ۱"),
            (86, 97, "سیستم‌های کنترل خطی"),
            (98, 109, "سیگنال‌ها و سیستم‌ها"),
            (110, 121, "الکترومغناطیس"),
            (122, 131, "مقدمه‌ای بر مهندسی زیست‌پزشکی"),
        ],
    },
    1402: {
        "pdf": INPUT_ROOT / "1402.pdf",
        "pages": INPUT_ROOT / "final1402",
        "booklet_code": "835C",
        "duration_minutes": 250,
        "answers": [
            3, 4, 1, 2, 1, 2, 4, 3, 2, 4, 1, 3, 2, 4, 2, 2, 1, 3, 4, 4,
            1, 3, 3, 4, 1, 3, 3, 2, 4, 3, 1, 1, 4, 2, 3, 2, 3, 3, 2, 4,
            2, 3, 2, 4, 2, 3, 3, 4, 1, 4, 1, 2, 3, 2, 3, 1, 4, 4, 3, 2,
            1, 2, 3, 2, 2, 3, 1, 4, 1, 2, 2, 3, 4, 2, 4, 1, 3, 1, 4, 4,
            4, 3, 2, 1, 3, 4, 4, 3, 2, 4, 1, 3, 1, 1, 2, 2, 3, 1, 4, 1,
            3, 2, 3, 2, 2, 4, 3, 3, 2, 2, 4, 3, 2, 1, 3, 4, 1, 4, 1, 2,
            4, 2, 2, 2, 3, 1, 2, 1, 3, 1, 3, 4, 4,
        ],
        "page_ranges": [
            (1, 7, 2), (8, 15, 3), (16, 20, 4), (21, 25, 5), (26, 29, 6),
            (30, 32, 7), (33, 36, 8), (37, 40, 9), (41, 45, 10), (46, 49, 11),
            (50, 52, 12), (53, 54, 13), (55, 58, 14), (59, 61, 15), (62, 65, 16),
            (66, 67, 17), (68, 69, 18), (70, 74, 19), (75, 78, 20), (79, 81, 21),
            (82, 85, 22), (86, 90, 23), (91, 92, 24), (93, 93, 25), (94, 94, 26),
            (95, 96, 27), (97, 99, 28), (100, 103, 29), (104, 108, 30),
            (109, 112, 31), (113, 116, 32), (117, 120, 33), (121, 124, 34),
            (125, 129, 35), (130, 133, 36),
        ],
        "subject_ranges": [
            (1, 25, "زبان عمومی و تخصصی (انگلیسی)"),
            (26, 40, "ریاضیات"),
            (41, 55, "مدارهای الکتریکی ۱ و ۲"),
            (56, 70, "الکترونیک ۱ و ۲ و سیستم‌های دیجیتال ۱"),
            (71, 85, "ماشین‌های الکتریکی ۱ و ۲ و تحلیل سیستم‌های انرژی الکتریکی ۱"),
            (86, 97, "سیستم‌های کنترل خطی"),
            (98, 109, "سیگنال‌ها و سیستم‌ها"),
            (110, 121, "الکترومغناطیس"),
            (122, 133, "مقدمه‌ای بر مهندسی زیست‌پزشکی"),
        ],
    },
}


def find_value(number, ranges, name):
    for start, end, value in ranges:
        if start <= number <= end:
            return value
    raise ValueError(f"No {name} for question {number}")


def build(year, config):
    answers = config["answers"]
    total = len(answers)
    if any(answer not in {1, 2, 3, 4} for answer in answers):
        raise ValueError(f"Invalid answer in {year}")

    pdf_name = f"arshad_bargh_{year}_1251.pdf"
    pdf_target = ROOT / "assets" / "source" / pdf_name
    questions_dir = ROOT / "assets" / "questions" / str(year)
    questions_dir.mkdir(parents=True, exist_ok=True)
    pdf_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(config["pdf"], pdf_target)

    questions = []
    key_answers = []
    for number, correct_answer in enumerate(answers, 1):
        page = find_value(number, config["page_ranges"], "page")
        lesson = find_value(number, config["subject_ranges"], "subject")
        image_name = f"question_{number:03d}.png"
        source_image = config["pages"] / f"page-{page:02d}.png"
        shutil.copy2(source_image, questions_dir / image_name)
        questions.append({
            "number": number,
            "subject": lesson,
            "image": f"assets/questions/{year}/{image_name}",
            "source_page": page,
            "choices": [1, 2, 3, 4],
            "correct_answer": correct_answer,
            "explanation": None,
            "explanation_status": "pending_review",
            "explanation_sources": [],
        })
        key_answers.append({"question_number": number, "correct_option": correct_answer, "lesson": lesson})

    source_pdf = f"assets/source/{pdf_name}"
    exam = {
        "exam_code": "1251",
        "year": year,
        "title": f"آزمون کارشناسی ارشد مهندسی برق {year}",
        "booklet_code": config["booklet_code"],
        "total_questions": total,
        "duration_minutes": config["duration_minutes"],
        "source_pdf": source_pdf,
        "image_policy": "Each question has a lossless copy of its complete official source page to avoid cutting formulas, diagrams, passages, or choices.",
        "questions": questions,
    }
    key = {
        "exam_code": "1251",
        "year": year,
        "booklet_code": config["booklet_code"],
        "total_questions": total,
        "source": "Initial Sanjesh answer-key page included in the source PDF",
        "source_pdf": source_pdf,
        "answers": key_answers,
    }
    (ROOT / "data" / "questions" / f"exam_{year}.json").write_text(
        json.dumps(exam, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "data" / "answer_keys" / f"key_{year}.json").write_text(
        json.dumps(key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    for exam_year, exam_config in EXAMS.items():
        build(exam_year, exam_config)
