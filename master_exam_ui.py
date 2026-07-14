import json
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).parent
st.set_page_config(page_title="آزمون کارشناسی ارشد", page_icon="🎓", layout="wide")
st.markdown("""
<style>
html, body, [class*="css"] { direction: rtl; text-align: right; }
[data-testid="stSidebar"] { left: auto; right: 0; }
[data-testid="stSidebar"] > div:first-child { right: 0; }
[data-testid="stImage"] { padding: .8rem; border: 1px solid #d9dee8; border-radius: 12px; background: white; }
[data-testid="stImage"] img { border-radius: 8px; background: white; }
.stButton button { width: 100%; min-height: 2.6rem; }
.correct { padding: 1rem; border-radius: .7rem; background:#dcfce7; color:#166534; }
.wrong { padding: 1rem; border-radius: .7rem; background:#fee2e2; color:#991b1b; }
.legend { font-size:.82rem; line-height:2; }
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] { gap: .18rem; }
[data-testid="stSidebar"] .stButton button {
    min-height: 2rem;
    padding: .1rem .15rem;
    font-size: .78rem;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_exams():
    result = []
    for path in sorted((ROOT / "data/questions").rglob("exam_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("questions"):
            result.append((path, data))
    return result


def source_pdfs(exam):
    source = exam.get("source", {})
    question_value = source.get("questions_pdf") or exam.get("source_pdf")
    answer_value = source.get("answer_key_pdf")
    return (
        ROOT / question_value if question_value else None,
        ROOT / answer_value if answer_value else None,
    )


@st.cache_data
def load_explanation_resources():
    path = ROOT / "data/explanation_resources.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


exams = load_exams()
if not exams:
    st.error("داده آزمون پیدا نشد.")
    st.stop()

labels = [data["title"] for _, data in exams]
selected_title = st.sidebar.selectbox("آزمون", labels, index=labels.index(next((x for x in labels if "۱۴۰۴" in x or "1404" in x), labels[0])))
exam_path, exam = exams[labels.index(selected_title)]
exam_id = str(exam_path.relative_to(ROOT))
questions = exam["questions"]
explanation_resources = load_explanation_resources().get(exam_id, [])

if st.session_state.get("exam_id") != exam_id:
    st.session_state.exam_id = exam_id
    st.session_state.answers = {}
    st.session_state.checked = {}
    st.session_state.pop("result_summary", None)
    st.session_state.question_number = questions[0]["number"]

subjects = list(dict.fromkeys(item["subject"] for item in questions))
current_number = st.session_state.get("question_number", questions[0]["number"])
current_question = next((q for q in questions if q["number"] == current_number), questions[0])
default_subject = subjects.index(current_question["subject"])
subject = st.sidebar.radio("صفحه درس", subjects, index=default_subject)
subject_questions = [q for q in questions if q["subject"] == subject]
if current_question["subject"] != subject:
    st.session_state.question_number = subject_questions[0]["number"]
    current_question = subject_questions[0]

st.sidebar.markdown("### پاسخ‌نامه")
st.sidebar.markdown(
    '<div class="legend">□ نزده &nbsp; ■ انتخاب‌شده &nbsp; 🟩 صحیح &nbsp; 🟥 غلط</div>',
    unsafe_allow_html=True,
)
header = st.sidebar.columns([1.25, 1, 1, 1, 1])
header[0].markdown("**سؤال**")
for option, column in enumerate(header[1:], 1):
    column.markdown(f"**{option}**")

for item in subject_questions:
    number = item["number"]
    answer = st.session_state.answers.get(number, 0)
    has_result = number in st.session_state.checked
    correct = item.get("correct_answer")
    columns = st.sidebar.columns([1.25, 1, 1, 1, 1])
    if columns[0].button(str(number), key=f"nav_{exam_id}_{number}"):
        st.session_state.question_number = number
        st.rerun()
    for option, column in enumerate(columns[1:], 1):
        if has_result and option == correct:
            label = "🟩"
        elif has_result and option == answer and answer != correct:
            label = "🟥"
        elif option == answer:
            label = "■"
        else:
            label = "□"
        if column.button(label, key=f"sheet_{exam_id}_{number}_{option}"):
            st.session_state.answers[number] = option
            st.session_state.question_number = number
            st.session_state.checked.pop(number, None)
            st.session_state.pop("result_summary", None)
            st.rerun()

answered_total = sum(bool(st.session_state.answers.get(q["number"], 0)) for q in questions)
st.sidebar.metric("پاسخ‌داده‌شده", f"{answered_total} از {len(questions)}")
st.sidebar.progress(answered_total / len(questions))

question = next(q for q in subject_questions if q["number"] == st.session_state.question_number)
position = subject_questions.index(question)

st.title(exam["title"])
st.caption(f"کد مجموعه {exam['exam_code']} | {len(questions)} سؤال")
question_pdf, answer_pdf = source_pdfs(exam)
download_columns = st.columns(2)
if question_pdf and question_pdf.exists():
    with question_pdf.open("rb") as file:
        download_columns[0].download_button("دانلود PDF سؤال‌ها", file, question_pdf.name, "application/pdf")
if answer_pdf and answer_pdf.exists():
    with answer_pdf.open("rb") as file:
        download_columns[1].download_button("دانلود PDF کلید", file, answer_pdf.name, "application/pdf")
st.markdown(f"## {subject}")
st.markdown(f"### سؤال {question['number']} از {subject_questions[-1]['number']}")

if question.get("context"):
    with st.expander("متن مشترک سؤال", expanded=True):
        st.markdown(question["context"])
if question.get("context_images"):
    with st.expander("متن مشترک سؤال", expanded=True):
        for context_image in question["context_images"]:
            st.image(str(ROOT / context_image), width="stretch")
if question.get("text"):
    st.markdown(question["text"])
else:
    st.image(str(ROOT / question["image"]), width="stretch")

choice_values = question.get("choice_texts") or [1, 2, 3, 4]
current = st.session_state.answers.get(question["number"], 0)
selected = st.radio(
    "پاسخ شما",
    [0, 1, 2, 3, 4],
    index=current,
    format_func=lambda value: "نزده" if value == 0 else (
        f"{value}) {choice_values[value - 1]}" if question.get("choice_texts") else f"گزینه {value}"
    ),
    key=f"answer_{exam_id}_{question['number']}",
)
if selected != current:
    st.session_state.checked.pop(question["number"], None)
    st.session_state.pop("result_summary", None)
st.session_state.answers[question["number"]] = selected

previous_col, next_col = st.columns(2)
if position > 0 and previous_col.button("سؤال قبلی"):
    st.session_state.question_number = subject_questions[position - 1]["number"]
    st.rerun()
if position + 1 < len(subject_questions) and next_col.button("سؤال بعدی", type="primary"):
    st.session_state.question_number = subject_questions[position + 1]["number"]
    st.rerun()

if st.button("ثبت و مشاهده پاسخ درست", disabled=selected == 0):
    correct = question.get("correct_answer")
    st.session_state.checked[question["number"]] = (selected == correct) if correct else None
    st.rerun()

if question["number"] in st.session_state.checked:
    correct = question.get("correct_answer")
    if correct is None:
        st.warning("این سؤال در کلید رسمی حذف شده است.")
    elif selected == correct:
        st.markdown(f'<div class="correct">✅ پاسخ درست است؛ گزینه {correct}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="wrong">❌ پاسخ نادرست است؛ پاسخ صحیح گزینه {correct}</div>', unsafe_allow_html=True)
    with st.expander("پاسخ تشریحی", expanded=True):
        if question.get("explanation_status") == "verified" and question.get("explanation"):
            st.markdown(question["explanation"])
            for source in question.get("explanation_sources", []):
                if isinstance(source, dict):
                    title = source.get("title") or source.get("url") or "منبع"
                    url = source.get("url")
                    st.caption(f"منبع: [{title}]({url})" if url else f"منبع: {title}")
                else:
                    st.caption(f"منبع: {source}")
        else:
            st.info("پاسخ تشریحی هنوز تهیه و بازبینی نشده است.")
            if explanation_resources:
                st.markdown("**منابع پیدا‌شده برای بررسی و تکمیل این آزمون:**")
                for resource in explanation_resources:
                    st.markdown(f"- [{resource['title']}]({resource['url']}) — {resource['coverage']}")

st.divider()
if st.button("محاسبه نتیجه آزمون"):
    graded = [q for q in questions if q.get("correct_answer") in {1, 2, 3, 4}]
    correct_count = wrong_count = empty_count = 0
    for item in graded:
        answer = st.session_state.answers.get(item["number"], 0)
        if not answer:
            empty_count += 1
        elif answer == item["correct_answer"]:
            correct_count += 1
        else:
            wrong_count += 1
    percent = (correct_count - wrong_count / 3) / len(graded) * 100 if graded else 0
    for item in graded:
        answer = st.session_state.answers.get(item["number"], 0)
        if answer:
            st.session_state.checked[item["number"]] = answer == item["correct_answer"]
    st.session_state.result_summary = (correct_count, wrong_count, empty_count, percent)
    st.rerun()

if st.session_state.get("result_summary"):
    correct_count, wrong_count, empty_count, percent = st.session_state.result_summary
    a, b, c, d = st.columns(4)
    a.metric("درست", correct_count)
    b.metric("غلط", wrong_count)
    c.metric("نزده", empty_count)
    d.metric("درصد", f"{percent:.2f}%")
