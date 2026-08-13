import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PDF = ROOT / "assets" / "source" / "arshad_bargh_1405_1251.pdf"
QUESTIONS_DIR = ROOT / "assets" / "questions" / "1405"
DATA_TARGET = ROOT / "data" / "questions" / "exam_1405.json"

PAGE_RANGES = [
    (1, 10, 2),
    (11, 15, 3),
    (16, 20, 4),
    (21, 26, 5),
    (27, 30, 6),
    (31, 33, 7),
    (34, 37, 8),
    (38, 41, 9),
    (42, 45, 10),
    (46, 49, 11),
    (50, 54, 12),
    (55, 58, 13),
    (59, 61, 14),
    (62, 64, 15),
    (65, 67, 16),
    (68, 70, 17),
    (71, 73, 18),
    (74, 77, 19),
    (78, 81, 20),
    (82, 84, 21),
    (85, 88, 22),
    (89, 91, 23),
    (92, 93, 24),
    (94, 96, 25),
    (97, 101, 26),
    (102, 106, 27),
    (107, 113, 28),
    (114, 121, 29),
    (122, 125, 30),
    (126, 129, 31),
    (130, 137, 32),
    (138, 140, 33),
]

SUBJECT_RANGES = [
    (1, 25, "زبان عمومی و تخصصی (انگلیسی)"),
    (26, 40, "ریاضیات"),
    (41, 55, "مدارهای الکتریکی ۱ و ۲"),
    (56, 70, "الکترونیک ۱ و ۲ و سیستم‌های دیجیتال ۱"),
    (71, 85, "ماشین‌های الکتریکی ۱ و ۲ و تحلیل سیستم‌های انرژی الکتریکی ۱"),
    (86, 95, "سیستم‌های کنترل خطی"),
    (96, 120, "سیگنال‌ها و سیستم‌ها و مخابرات"),
    (121, 130, "الکترومغناطیس"),
    (131, 140, "مقدمه‌ای بر مهندسی زیست‌پزشکی"),
]


def find_value(number: int, ranges, label: str):
    for start, end, value in ranges:
        if start <= number <= end:
            return value
    raise ValueError(f"No {label} for question {number}")


def render_pages(target: Path) -> dict[int, Path]:
    subprocess.check_call([
        "pdftoppm",
        "-f", "2",
        "-l", "33",
        "-r", "180",
        "-png",
        str(SOURCE_PDF),
        str(target / "page"),
    ])
    pages = {}
    for path in target.glob("page-*.png"):
        page = int(path.stem.rsplit("-", 1)[1])
        pages[page] = path
    expected = set(range(2, 34))
    if set(pages) != expected:
        raise RuntimeError(f"Rendered pages mismatch: {sorted(pages)}")
    return pages


def update_ui() -> None:
    path = ROOT / "master_exam_ui.py"
    text = path.read_text(encoding="utf-8")

    old_default = 'selected_title = st.sidebar.selectbox("آزمون", labels, index=labels.index(next((x for x in labels if "۱۴۰۴" in x or "1404" in x), labels[0])))'
    new_default = 'default_exam_index = max(range(len(exams)), key=lambda index: int(exams[index][1].get("year", 0)))\nselected_title = st.sidebar.selectbox("آزمون", labels, index=default_exam_index)'
    if old_default in text:
        text = text.replace(old_default, new_default)

    old_questions = 'questions = exam["questions"]\nexplanation_resources = load_explanation_resources().get(exam_id, [])'
    new_questions = 'questions = exam["questions"]\nhas_official_key = any(question.get("correct_answer") in {1, 2, 3, 4} for question in questions)\nexplanation_resources = load_explanation_resources().get(exam_id, [])'
    if old_questions in text:
        text = text.replace(old_questions, new_questions)

    old_graded = '''def calculate_subject_result(subject_name, all_questions, answers):
    graded = [
        question for question in all_questions
        if question.get("subject") == subject_name and question.get("correct_answer") in {1, 2, 3, 4}
    ]'''
    new_graded = '''def calculate_subject_result(subject_name, all_questions, answers):
    subject_aliases = {
        "سیگنال‌ها و سیستم‌ها": {"سیگنال‌ها و سیستم‌ها", "سیگنال‌ها و سیستم‌ها و مخابرات"},
    }
    accepted_subjects = subject_aliases.get(subject_name, {subject_name})
    graded = [
        question for question in all_questions
        if question.get("subject") in accepted_subjects and question.get("correct_answer") in {1, 2, 3, 4}
    ]'''
    if old_graded in text:
        text = text.replace(old_graded, new_graded)

    old_disabled = '        disabled=selected == 0,\n        key=f"check_{exam_id}_{question[\'number\']}",'
    new_disabled = '        disabled=selected == 0 or question.get("correct_answer") not in {1, 2, 3, 4},\n        key=f"check_{exam_id}_{question[\'number\']}",'
    if old_disabled in text:
        text = text.replace(old_disabled, new_disabled)

    marker = 'if question["number"] in st.session_state.checked:'
    info = 'if question.get("correct_answer") not in {1, 2, 3, 4}:\n    st.info("کلید رسمی این آزمون هنوز اضافه نشده است.")\n\n'
    if info not in text and marker in text:
        text = text.replace(marker, info + marker)

    text = text.replace('if st.button("مشاهده نتایج"):', 'if st.button("مشاهده نتایج", disabled=not has_official_key):')

    required = [
        "default_exam_index",
        "has_official_key",
        "کلید رسمی این آزمون هنوز اضافه نشده است.",
        "سیگنال‌ها و سیستم‌ها و مخابرات",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError(f"UI patch incomplete: {missing}")
    path.write_text(text, encoding="utf-8")


def update_readme() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "برای سال‌های ۱۴۰۲، ۱۴۰۳ و ۱۴۰۴.",
        "برای سال‌های ۱۴۰۲، ۱۴۰۳، ۱۴۰۴ و ۱۴۰۵.",
    )
    text = text.replace(
        "| سال | کد دفترچه | تعداد سؤال | PDF و کلید | تصاویر سؤال |",
        "| سال | کد دفترچه | تعداد سؤال | وضعیت PDF / کلید | تصاویر سؤال |",
    )
    row_1404 = "| ۱۴۰۴ | `535C` | ۱۲۵ | موجود | ۱۲۵ |"
    row_1405 = "| ۱۴۰۵ | `335A` | ۱۴۰ | PDF سؤال موجود؛ کلید در انتظار | ۱۴۰ |"
    if row_1405 not in text:
        text = text.replace(row_1404, row_1404 + "\n" + row_1405)
    text = text.replace(
        "اسکریپت‌های `tools/build_exam_1404.py` و `tools/build_exam_years.py` ساخت داده‌ها را مستند می‌کنند.",
        "اسکریپت‌های `tools/build_exam_1404.py`، `tools/build_exam_1405.py` و `tools/build_exam_years.py` ساخت داده‌ها را مستند می‌کنند.",
    )
    if row_1405 not in text:
        raise RuntimeError("README patch incomplete")
    path.write_text(text, encoding="utf-8")


def validate_questions(questions: list[dict]) -> None:
    if len(questions) != 140:
        raise RuntimeError("Expected 140 questions")
    if [item["number"] for item in questions] != list(range(1, 141)):
        raise RuntimeError("Question numbers are not contiguous")
    for question in questions:
        image = ROOT / question["image"]
        if not image.exists() or image.stat().st_size == 0:
            raise FileNotFoundError(image)
        with Image.open(image) as rendered:
            rendered.verify()
        if question["correct_answer"] is not None:
            raise RuntimeError("1405 answer key must remain empty until the official key is added")


def main() -> None:
    if not SOURCE_PDF.exists() or SOURCE_PDF.stat().st_size == 0:
        raise FileNotFoundError(SOURCE_PDF)

    if QUESTIONS_DIR.exists():
        shutil.rmtree(QUESTIONS_DIR)
    QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_TARGET.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="exam-1405-pages-") as temp:
        rendered_pages = render_pages(Path(temp))
        questions = []
        for number in range(1, 141):
            page = find_value(number, PAGE_RANGES, "source page")
            subject = find_value(number, SUBJECT_RANGES, "subject")
            image_name = f"question_{number:03d}.png"
            shutil.copy2(rendered_pages[page], QUESTIONS_DIR / image_name)
            questions.append({
                "number": number,
                "subject": subject,
                "image": f"assets/questions/1405/{image_name}",
                "source_page": page,
                "choices": [1, 2, 3, 4],
                "correct_answer": None,
                "explanation": None,
                "explanation_status": "pending_review",
                "explanation_sources": [],
            })

    exam = {
        "exam_code": "1251",
        "year": 1405,
        "title": "آزمون کارشناسی ارشد مهندسی برق ۱۴۰۵",
        "booklet_code": "335A",
        "total_questions": 140,
        "duration_minutes": 250,
        "answer_key_status": "pending_official_key",
        "source_pdf": "assets/source/arshad_bargh_1405_1251.pdf",
        "image_policy": "Each question has a lossless PNG copy of its complete official source page to avoid cutting formulas, diagrams, passages, or choices.",
        "questions": questions,
    }
    DATA_TARGET.write_text(json.dumps(exam, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    update_ui()
    update_readme()
    validate_questions(questions)
    print("Built and validated the complete 1405 question set")


if __name__ == "__main__":
    main()
