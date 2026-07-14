import json
import time
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent

st.set_page_config(page_title="آزمون‌های کارشناسی ارشد", page_icon="🎓", layout="wide")
st.markdown("""
<style>
html, body, [class*="css"] { direction: rtl; text-align: right; }
[data-testid="stImage"] img { border: 1px solid #ddd; border-radius: 12px; }
.stButton button { width: 100%; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_exams():
    paths = sorted((ROOT / "data" / "questions").rglob("exam_*.json"))
    return [(path, json.loads(path.read_text(encoding="utf-8"))) for path in paths]


available = load_exams()
labels = [exam["title"] for _, exam in available]
selected_label = st.sidebar.selectbox("آزمون", labels)
exam_path, exam = available[labels.index(selected_label)]
questions = exam["questions"]
exam_id = str(exam_path.relative_to(ROOT))

if st.session_state.get("exam_id") != exam_id:
    st.session_state.exam_id = exam_id
    st.session_state.answers = {}
    st.session_state.started_at = time.time()

st.title(exam["title"])
st.caption(f"کد مجموعه {exam['exam_code']} | کد دفترچه {exam['booklet_code']} | {exam['total_questions']} سؤال")

source = exam.get("source", {})
question_pdf = ROOT / source.get("questions_pdf", "assets/source/arshad_bargh_1404_1251.pdf")
answer_pdf_value = source.get("answer_key_pdf")
if question_pdf.exists():
    with question_pdf.open("rb") as file:
        st.download_button("دانلود PDF سؤال‌ها", file, question_pdf.name, "application/pdf")
if answer_pdf_value:
    answer_pdf = ROOT / answer_pdf_value
    if answer_pdf.exists():
        with answer_pdf.open("rb") as file:
            st.download_button("دانلود PDF کلید پاسخ", file, answer_pdf.name, "application/pdf")

subject_names = list(dict.fromkeys(q["subject"] for q in questions))
selected_subject = st.sidebar.selectbox("درس", ["همه درس‌ها", *subject_names])
visible = questions if selected_subject == "همه درس‌ها" else [q for q in questions if q["subject"] == selected_subject]
question_numbers = [q["number"] for q in visible]
requested = st.session_state.pop("requested_question", None)
selected_index = question_numbers.index(requested) if requested in question_numbers else 0
selected_number = st.sidebar.selectbox("شماره سؤال", question_numbers, index=selected_index)
question = next(q for q in questions if q["number"] == selected_number)

answered = sum(value in {1, 2, 3, 4} for value in st.session_state.answers.values())
st.sidebar.metric("پاسخ‌داده‌شده", f"{answered} از {len(questions)}")
st.subheader(f"سؤال {question['number']} - {question['subject']}")
st.image(str(ROOT / question["image"]), use_container_width=True)
st.caption(f"صفحه {question['source_page']} دفترچه؛ صفحه کامل نگه‌داری شده تا فرمول، نمودار یا گزینه بریده نشود.")

current = st.session_state.answers.get(question["number"])
options = ["نزده", "گزینه ۱", "گزینه ۲", "گزینه ۳", "گزینه ۴"]
selected = st.radio("پاسخ شما", options, index=0 if current is None else int(current), horizontal=True, key=f"answer_{exam_id}_{question['number']}")
st.session_state.answers[question["number"]] = 0 if selected == "نزده" else options.index(selected)

left, right = st.columns(2)
with right:
    previous = [n for n in question_numbers if n < selected_number]
    if previous and st.button("سؤال قبلی"):
        st.session_state.requested_question = previous[-1]
        st.rerun()
with left:
    following = [n for n in question_numbers if n > selected_number]
    if following and st.button("سؤال بعدی"):
        st.session_state.requested_question = following[0]
        st.rerun()

st.divider()
if st.button("محاسبه نتیجه فعلی"):
    graded = [item for item in questions if item.get("correct_answer") in {1, 2, 3, 4}]
    deleted = len(questions) - len(graded)
    correct = wrong = empty = 0
    for item in graded:
        user_answer = st.session_state.answers.get(item["number"], 0)
        if user_answer == 0: empty += 1
        elif user_answer == item["correct_answer"]: correct += 1
        else: wrong += 1
    percent = ((correct - wrong / 3) / len(graded)) * 100 if graded else 0
    cols = st.columns(5 if deleted else 4)
    cols[0].metric("درست", correct); cols[1].metric("غلط", wrong); cols[2].metric("نزده", empty)
    if deleted: cols[3].metric("حذف‌شده", deleted)
    cols[-1].metric("درصد با نمره منفی", f"{percent:.2f}%")

    with st.expander("پاسخ صحیح و توضیح"):
        if question.get("correct_answer") is None:
            st.warning("این سؤال در کلید نهایی حذف شده است.")
        else:
            st.write("پاسخ صحیح:", f"گزینه {question['correct_answer']}")
            if question.get("explanation_status") == "verified": st.write(question["explanation"])
            else: st.info("پاسخ تشریحی این سؤال هنوز تهیه و بازبینی نشده است.")
