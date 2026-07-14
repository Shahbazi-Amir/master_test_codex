import json
import time
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).parent
AVAILABLE_YEARS = [1404, 1403, 1402]

st.set_page_config(page_title="آزمون ارشد مهندسی برق", page_icon="⚡", layout="wide")
st.markdown(
    """
    <style>
    html, body, [class*="css"] { direction: rtl; text-align: right; }
    [data-testid="stImage"] img { border: 1px solid #ddd; border-radius: 12px; }
    .stButton button { width: 100%; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_exam(year: int) -> dict:
    exam_path = ROOT / "data" / "questions" / f"exam_{year}.json"
    return json.loads(exam_path.read_text(encoding="utf-8"))


selected_year = st.sidebar.selectbox("سال آزمون", AVAILABLE_YEARS)
exam = load_exam(selected_year)
questions = exam["questions"]
source_pdf = ROOT / exam["source_pdf"]

answers_key = f"answers_{selected_year}"
started_key = f"started_at_{selected_year}"
if answers_key not in st.session_state:
    st.session_state[answers_key] = {}
if started_key not in st.session_state:
    st.session_state[started_key] = time.time()
answers = st.session_state[answers_key]

st.title(exam["title"])
st.caption(f"کد مجموعه {exam['exam_code']} | کد دفترچه {exam['booklet_code']} | {exam['total_questions']} سؤال")

with source_pdf.open("rb") as pdf_file:
    st.download_button(
        "دانلود PDF رسمی سؤال‌ها و کلید",
        data=pdf_file,
        file_name=source_pdf.name,
        mime="application/pdf",
    )

subject_names = list(dict.fromkeys(q["subject"] for q in questions))
selected_subject = st.sidebar.selectbox("درس", ["همه درس‌ها", *subject_names])
visible = questions if selected_subject == "همه درس‌ها" else [q for q in questions if q["subject"] == selected_subject]
question_numbers = [q["number"] for q in visible]
requested = st.session_state.pop("requested_question", None)
selected_index = question_numbers.index(requested) if requested in question_numbers else 0
selected_number = st.sidebar.selectbox("شماره سؤال", question_numbers, index=selected_index)
question = next(q for q in questions if q["number"] == selected_number)

answered = sum(1 for value in answers.values() if value in {1, 2, 3, 4})
st.sidebar.metric("پاسخ‌داده‌شده", f"{answered} از {len(questions)}")

st.subheader(f"سؤال {question['number']} - {question['subject']}")
st.image(str(ROOT / question["image"]), use_container_width=True)
st.caption(f"صفحه {question['source_page']} دفترچه رسمی؛ صفحه کامل نگه‌داری شده تا هیچ فرمول، نمودار یا گزینه‌ای بریده نشود.")

current = answers.get(question["number"])
options = ["نزده", "گزینه ۱", "گزینه ۲", "گزینه ۳", "گزینه ۴"]
selected = st.radio(
    "پاسخ شما",
    options,
    index=0 if current is None else int(current),
    horizontal=True,
    key=f"answer_{selected_year}_{question['number']}",
)
answers[question["number"]] = 0 if selected == "نزده" else options.index(selected)

left, right = st.columns(2)
previous_numbers = [n for n in question_numbers if n < selected_number]
next_numbers = [n for n in question_numbers if n > selected_number]
with right:
    if previous_numbers and st.button("سؤال قبلی"):
        st.session_state.requested_question = previous_numbers[-1]
        st.rerun()
with left:
    if next_numbers and st.button("سؤال بعدی"):
        st.session_state.requested_question = next_numbers[0]
        st.rerun()

st.divider()
if st.button("محاسبه نتیجه فعلی"):
    correct = wrong = empty = 0
    for item in questions:
        user_answer = answers.get(item["number"], 0)
        if user_answer == 0:
            empty += 1
        elif user_answer == item["correct_answer"]:
            correct += 1
        else:
            wrong += 1
    percent = ((correct - wrong / 3) / len(questions)) * 100
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("درست", correct)
    c2.metric("غلط", wrong)
    c3.metric("نزده", empty)
    c4.metric("درصد با نمره منفی", f"{percent:.2f}%")

    with st.expander("پاسخ صحیح و توضیح"):
        st.write("پاسخ صحیح:", f"گزینه {question['correct_answer']}")
        if question["explanation_status"] == "verified":
            st.write(question["explanation"])
        else:
            st.info("پاسخ تشریحی این سؤال هنوز تهیه و بازبینی نشده است.")
