import json
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="آزمون ارشد برق ۱۲۵۱", page_icon="⚡", layout="wide")

st.markdown(
    """
    <style>
    html, body, [class*="css"] { direction: rtl; text-align: right; }
    .stButton button { width: 100%; }
    .status-card {border:1px solid #ddd; border-radius:14px; padding:16px; margin:8px 0; background:#fafafa;}
    .danger-card {border:1px solid #e0b4b4; border-radius:14px; padding:16px; margin:8px 0; background:#fff6f6;}
    .ok-card {border:1px solid #b7d7b7; border-radius:14px; padding:16px; margin:8px 0; background:#f6fff6;}
    </style>
    """,
    unsafe_allow_html=True,
)

APP_ROOT = Path(__file__).parent
SOURCES_PATH = APP_ROOT / "data" / "sources" / "electrical_1251_sources.json"
QUESTIONS_DIR = APP_ROOT / "data" / "questions"
YEARS = list(range(1404, 1395, -1))
REQUIRED_FIELDS = {
    "year",
    "exam_code",
    "lesson",
    "question_number",
    "question_text",
    "options",
    "correct_option",
    "source_url",
    "source_type",
    "extraction_status",
}


def load_sources() -> list[dict]:
    if not SOURCES_PATH.exists():
        return []
    try:
        payload = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return payload.get("years", []) if isinstance(payload, dict) else []


def load_verified_questions(year: int) -> list[dict]:
    if not QUESTIONS_DIR.exists():
        return []
    questions: list[dict] = []
    for path in sorted(QUESTIONS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        records = data if isinstance(data, list) else data.get("questions", []) if isinstance(data, dict) else []
        for record in records:
            if not isinstance(record, dict):
                continue
            if record.get("year") != year:
                continue
            if record.get("exam_code") != "1251":
                continue
            if record.get("extraction_status") != "extracted_verified":
                continue
            if not REQUIRED_FIELDS.issubset(record):
                continue
            if not isinstance(record.get("options"), list) or len(record["options"]) != 4:
                continue
            questions.append(record)
    return sorted(questions, key=lambda item: item["question_number"])


def calculate_score(answers: dict, questions: list[dict]) -> dict:
    correct = wrong = empty = 0
    rows = []
    for q in questions:
        number = q["question_number"]
        user_answer = answers.get(number)
        correct_option = int(q["correct_option"])
        if user_answer is None:
            status = "بدون پاسخ"
            empty += 1
        elif int(user_answer) == correct_option:
            status = "درست"
            correct += 1
        else:
            status = "غلط"
            wrong += 1
        rows.append({"شماره": number, "درس": q["lesson"], "وضعیت": status})
    total = len(questions)
    percent = ((correct - wrong / 3) / total * 100) if total else 0
    return {"correct": correct, "wrong": wrong, "empty": empty, "percent": percent, "rows": rows}


if "answers" not in st.session_state:
    st.session_state.answers = {}
if "finished" not in st.session_state:
    st.session_state.finished = False

st.title("سامانه شبیه‌ساز واقعی آزمون ارشد مهندسی برق")
st.caption("کد مجموعه ۱۲۵۱ | سیاست فعلی: سؤال نمونه و ساختگی در آزمون اصلی نمایش داده نمی‌شود.")

sources = load_sources()
source_by_year = {item.get("year"): item for item in sources}

selected_year = st.sidebar.selectbox("سال آزمون", YEARS)
mode = st.sidebar.radio("بخش", ["آزمون", "گزارش داده‌ها"])
questions = load_verified_questions(selected_year)
source = source_by_year.get(selected_year, {})

if mode == "گزارش داده‌ها":
    st.subheader("وضعیت داده‌های واقعی")
    rows = []
    for year in YEARS:
        item = source_by_year.get(year, {})
        qs = load_verified_questions(year)
        rows.append(
            {
                "سال": year,
                "کد آزمون": "1251",
                "وضعیت منبع": item.get("source_status", "ثبت نشده"),
                "سؤال استخراج‌شده قابل آزمون": len(qs),
                "نوع منبع": item.get("source_type", "نامشخص"),
                "وضعیت استخراج": item.get("extraction_status", "not_extracted"),
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.warning("تا وقتی سؤال و کلید با استخراج قابل اعتماد وارد نشود، آن سال برای آزمون فعال نمی‌شود.")
    if SOURCES_PATH.exists():
        with st.expander("مشاهده فایل منبع‌یابی"):
            st.code(SOURCES_PATH.read_text(encoding="utf-8"), language="json")
    st.stop()

st.subheader(f"آزمون سال {selected_year}")

if not questions:
    st.markdown(
        """
        <div class='danger-card'>
        <b>داده واقعی این سال هنوز وارد نشده است.</b><br>
        برای این سال هنوز سؤال‌هایی که هم متن سؤال، هم گزینه‌ها، هم کلید معتبر، و هم وضعیت
        <code>extracted_verified</code> داشته باشند در مخزن ثبت نشده‌اند.
        </div>
        """,
        unsafe_allow_html=True,
    )
    if source:
        st.write("وضعیت منبع:", source.get("source_status", "نامشخص"))
        st.write("وضعیت استخراج:", source.get("extraction_status", "not_extracted"))
        if source.get("notes"):
            st.info(source["notes"])
    st.stop()

if not st.session_state.finished:
    for q in questions:
        st.markdown(
            f"<div class='status-card'><b>سؤال {q['question_number']} - {q['lesson']}</b><br>{q['question_text']}</div>",
            unsafe_allow_html=True,
        )
        choice = st.radio(
            "گزینه را انتخاب کنید",
            q["options"],
            key=f"q_{selected_year}_{q['question_number']}",
            index=None,
        )
        if choice is not None:
            st.session_state.answers[q["question_number"]] = q["options"].index(choice) + 1
        st.divider()

    if st.button("پایان آزمون و مشاهده نتیجه"):
        st.session_state.finished = True
        st.rerun()
else:
    result = calculate_score(st.session_state.answers, questions)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("درست", result["correct"])
    c2.metric("غلط", result["wrong"])
    c3.metric("بدون پاسخ", result["empty"])
    c4.metric("درصد با نمره منفی", f"{result['percent']:.1f}%")
    st.dataframe(pd.DataFrame(result["rows"]), use_container_width=True, hide_index=True)

    st.subheader("مرور سؤال‌ها")
    for q in questions:
        user_answer = st.session_state.answers.get(q["question_number"])
        correct_option = int(q["correct_option"])
        if user_answer is None:
            icon, status = "⚪", "بدون پاسخ"
        elif int(user_answer) == correct_option:
            icon, status = "🟢", "درست"
        else:
            icon, status = "🔴", "غلط"
        with st.expander(f"{icon} سؤال {q['question_number']} - {status}"):
            st.write(q["question_text"])
            st.write("گزینه صحیح:", q["options"][correct_option - 1])
            if user_answer is not None:
                st.write("پاسخ شما:", q["options"][int(user_answer) - 1])
            if q.get("explanation"):
                st.info(q["explanation"])
            st.caption(f"منبع: {q.get('source_url', 'ثبت نشده')}")

    st.warning("رتبه و قبولی تا زمان ورود داده واقعی کافی و آمار معتبر فعال نمی‌شود.")
    if st.button("شروع دوباره"):
        st.session_state.answers = {}
        st.session_state.finished = False
        st.rerun()
