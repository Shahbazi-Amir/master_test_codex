import json
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent

st.set_page_config(page_title="سامانه آزمون کارشناسی ارشد", page_icon="🎓", layout="wide")
st.markdown("""
<style>
html, body, [class*="css"] { direction: rtl; text-align: right; }
[data-testid="stImage"] img { border: 1px solid #d9dee8; border-radius: 14px; background: white; }
.stButton button { width: 100%; }
.correct-answer { padding: 1rem; border-radius: .75rem; background: #dcfce7; color: #166534; }
.wrong-answer { padding: 1rem; border-radius: .75rem; background: #fee2e2; color: #991b1b; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_exams():
    exams = []
    for path in sorted((ROOT / "data" / "questions").rglob("exam_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("questions"):
            exams.append((path, data))
    return exams


def source_pdfs(exam):
    source = exam.get("source", {})
    question_value = source.get("questions_pdf") or exam.get("source_pdf")
    answer_value = source.get("answer_key_pdf")
    return (ROOT / question_value if question_value else None,
            ROOT / answer_value if answer_value else None)


available = load_exams()
if not available:
    st.error("هیچ داده آزمونی پیدا نشد.")
    st.stop()

labels = [exam["title"] for _, exam in available]
selected_label = st.sidebar.selectbox("انتخاب آزمون", labels)
exam_path, exam = available[labels.index(selected_label)]
questions = exam["questions"]
exam_id = str(exam_path.relative_to(ROOT))

if st.session_state.get("active_exam") != exam_id:
    st.session_state.active_exam = exam_id
    st.session_state.answers = {}
    st.session_state.checked = set()

st.title(exam["title"])
st.caption(f"کد مجموعه {exam['exam_code']} | کد دفترچه {exam['booklet_code']} | {exam['total_questions']} سؤال")

question_pdf, answer_pdf = source_pdfs(exam)
download_columns = st.columns(2)
if question_pdf and question_pdf.exists():
    with question_pdf.open("rb") as file:
        download_columns[0].download_button("دانلود PDF سؤال‌ها", file, question_pdf.name, "application/pdf")
if answer_pdf and answer_pdf.exists():
    with answer_pdf.open("rb") as file:
        download_columns[1].download_button("دانلود PDF کلید", file, answer_pdf.name, "application/pdf")

subjects = list(dict.fromkeys(q["subject"] for q in questions))
selected_subject = st.sidebar.selectbox("درس", ["همه درس‌ها", *subjects])
visible = questions if selected_subject == "همه درس‌ها" else [q for q in questions if q["subject"] == selected_subject]
numbers = [q["number"] for q in visible]
requested = st.session_state.pop("requested_question", None)
index = numbers.index(requested) if requested in numbers else 0
selected_number = st.sidebar.selectbox("شماره سؤال", numbers, index=index)
question = next(q for q in questions if q["number"] == selected_number)

answered = sum(value in {1, 2, 3, 4} for value in st.session_state.answers.values())
st.sidebar.metric("پاسخ‌داده‌شده", f"{answered} از {len(questions)}")
st.progress(answered / len(questions))

st.subheader(f"سؤال {question['number']} — {question['subject']}")
st.image(str(ROOT / question["image"]), use_container_width=True)

answer_key = (exam_id, question["number"])
current = st.session_state.answers.get(question["number"], 0)
choice = st.radio(
    "پاسخ شما",
    [0, 1, 2, 3, 4],
    index=current,
    format_func=lambda value: "نزده" if value == 0 else f"گزینه {value}",
    horizontal=True,
    key=f"choice_{exam_id}_{question['number']}",
)
st.session_state.answers[question["number"]] = choice

if st.button("بررسی پاسخ", type="primary", disabled=choice == 0):
    st.session_state.checked.add(answer_key)

if answer_key in st.session_state.checked:
    correct = question.get("correct_answer")
    if correct is None:
        st.warning("این سؤال در کلید نهایی حذف شده و در نمره محاسبه نمی‌شود.")
    elif choice == correct:
        st.markdown(f'<div class="correct-answer">✅ پاسخ درست است: گزینه {correct}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="wrong-answer">❌ پاسخ انتخابی نادرست است. پاسخ صحیح: گزینه {correct}</div>', unsafe_allow_html=True)
    st.markdown("#### پاسخ تشریحی")
    if question.get("explanation_status") == "verified" and question.get("explanation"):
        st.write(question["explanation"])
        for source in question.get("explanation_sources", []):
            st.caption(source)
    else:
        st.info("پاسخ تشریحی این سؤال هنوز تهیه و بازبینی نشده است.")

previous = [n for n in numbers if n < selected_number]
following = [n for n in numbers if n > selected_number]
left, right = st.columns(2)
with right:
    if previous and st.button("سؤال قبلی"):
        st.session_state.requested_question = previous[-1]
        st.rerun()
with left:
    if following and st.button("سؤال بعدی"):
        st.session_state.requested_question = following[0]
        st.rerun()

st.divider()
if st.button("محاسبه نتیجه کل آزمون"):
    graded = [q for q in questions if q.get("correct_answer") in {1, 2, 3, 4}]
    correct_count = wrong_count = empty_count = 0
    for item in graded:
        user_answer = st.session_state.answers.get(item["number"], 0)
        if user_answer == 0: empty_count += 1
        elif user_answer == item["correct_answer"]: correct_count += 1
        else: wrong_count += 1
    percent = ((correct_count - wrong_count / 3) / len(graded)) * 100 if graded else 0
    columns = st.columns(4)
    columns[0].metric("درست", correct_count)
    columns[1].metric("غلط", wrong_count)
    columns[2].metric("نزده", empty_count)
    columns[3].metric("درصد با نمره منفی", f"{percent:.2f}%")
