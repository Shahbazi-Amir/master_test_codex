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
.legend {
    display:flex;
    flex-wrap:wrap;
    gap:.35rem .65rem;
    align-items:center;
    font-size:.78rem;
    line-height:1.8;
}
.legend-item { display:inline-flex; align-items:center; gap:.2rem; white-space:nowrap; }
.legend-square {
    display:inline-block;
    width:.82rem;
    height:.82rem;
    border:1px solid #94a3b8;
    border-radius:2px;
    box-sizing:border-box;
}
.legend-square.empty { background:#fff; }
.legend-square.selected { background:#2563eb; border-color:#2563eb; }
.legend-square.correct { background:#22c55e; border-color:#22c55e; padding:0; }
.legend-square.wrong { background:#ef4444; border-color:#ef4444; padding:0; }
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] { gap: .12rem; align-items:center; }
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton button {
    width:2rem;
    height:2rem;
    min-height:2rem;
    padding:0;
    font-size:.78rem;
    line-height:1;
}
.answer-number {
    height:2rem;
    display:flex;
    align-items:center;
    justify-content:center;
    font-weight:700;
    direction:rtl;
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


def to_persian_digits(value):
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


ELECTRICAL_SUBJECTS = [
    "زبان عمومی و تخصصی (انگلیسی)",
    "ریاضیات",
    "مدارهای الکتریکی ۱ و ۲",
    "الکترونیک ۱ و ۲ و سیستم‌های دیجیتال ۱",
    "ماشین‌های الکتریکی ۱ و ۲ و تحلیل سیستم‌های انرژی الکتریکی ۱",
    "سیستم‌های کنترل خطی",
    "سیگنال‌ها و سیستم‌ها",
    "الکترومغناطیس",
]
BIOMEDICAL_SUBJECT = "مقدمه‌ای بر مهندسی زیست‌پزشکی"
ELECTRICAL_COEFFICIENT_CODES = {
    "کد ضریب ۱ — الکترونیک": [2, 3, 3, 4, 1, 1, 2, 2],
    "کد ضریب ۲ — قدرت": [2, 3, 3, 1, 4, 2, 1, 1],
    "کد ضریب ۳": [2, 3, 3, 2, 1, 1, 2, 4],
    "کد ضریب ۴": [2, 3, 3, 2, 1, 1, 4, 2],
    "کد ضریب ۵ — کنترل": [2, 3, 3, 1, 2, 4, 2, 1],
    "کد ضریب ۶ — زیست‌پزشکی": [2, 3, 3, 3, 1, 4, 4, 1],
    "کد ضریب ۷": [2, 3, 3, 4, 4, 4, 1, 1],
    "کد ضریب ۸": [2, 3, 3, 2, 1, 2, 1, 4],
    "کد ضریب ۹": [2, 4, 3, 3, 0, 0, 4, 4],
    "کد ضریب ۱۰": [2, 3, 3, 3, 1, 4, 4, 1],
}


def calculate_subject_result(subject_name, all_questions, answers):
    graded = [
        question for question in all_questions
        if question.get("subject") == subject_name and question.get("correct_answer") in {1, 2, 3, 4}
    ]
    correct = wrong = empty = 0
    for question in graded:
        answer = answers.get(question["number"], 0)
        if not answer:
            empty += 1
        elif answer == question["correct_answer"]:
            correct += 1
        else:
            wrong += 1
    raw_score = 3 * correct - wrong
    percent = raw_score / (3 * len(graded)) * 100 if graded else 0
    return {"correct": correct, "wrong": wrong, "empty": empty, "raw": raw_score, "percent": percent}


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
    """
    <div class="legend">
      <span class="legend-item"><span class="legend-square empty"></span>نزده</span>
      <span class="legend-item"><span class="legend-square selected"></span>انتخاب‌شده</span>
      <span class="legend-item"><span class="legend-square correct"></span>صحیح</span>
      <span class="legend-item"><span class="legend-square wrong"></span>غلط</span>
    </div>
    """,
    unsafe_allow_html=True,
)
header = st.sidebar.columns([1.15, .72, 1, 1, 1, 1])
header[0].markdown("**شماره**")
header[1].markdown("")
for option, column in enumerate(header[2:], 1):
    column.markdown(f"**{to_persian_digits(option)}**")

for item in subject_questions:
    number = item["number"]
    answer = st.session_state.answers.get(number, 0)
    has_result = number in st.session_state.checked
    correct = item.get("correct_answer")
    columns = st.sidebar.columns([1.15, .72, 1, 1, 1, 1])
    columns[0].markdown(
        f'<div class="answer-number">{to_persian_digits(number)}</div>',
        unsafe_allow_html=True,
    )
    switch_label = "●" if number == st.session_state.question_number else "○"
    if columns[1].button(switch_label, key=f"nav_{exam_id}_{number}", help=f"رفتن به سؤال {to_persian_digits(number)}"):
        st.session_state.question_number = number
        st.rerun()
    for option, column in enumerate(columns[2:], 1):
        if has_result and option == correct:
            label = "🟩"
        elif has_result and option == answer and answer != correct:
            label = "🟥"
        elif option == answer:
            label = "🟦"
        else:
            label = "⬜"
        if column.button(label, key=f"sheet_{exam_id}_{number}_{option}", help=f"گزینه {to_persian_digits(option)}"):
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
st.markdown(f"### سؤال {to_persian_digits(question['number'])} از {to_persian_digits(subject_questions[-1]['number'])}")

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
        f"{to_persian_digits(value)}) {choice_values[value - 1]}" if question.get("choice_texts") else f"گزینه {to_persian_digits(value)}"
    ),
    key=f"answer_{exam_id}_{question['number']}",
)
if selected != current:
    st.session_state.checked.pop(question["number"], None)
    st.session_state.pop("result_summary", None)
st.session_state.answers[question["number"]] = selected

if st.button(
    "سؤال بعدی",
    type="primary",
    disabled=position + 1 >= len(subject_questions),
    key=f"next_{exam_id}_{question['number']}",
):
    st.session_state.question_number = subject_questions[position + 1]["number"]
    st.rerun()

if st.button(
    "سؤال قبلی",
    disabled=position == 0,
    key=f"previous_{exam_id}_{question['number']}",
):
    st.session_state.question_number = subject_questions[position - 1]["number"]
    st.rerun()

answer_left, answer_center, answer_right = st.columns([1, 2, 1])
with answer_center:
    if st.button(
        "ثبت و مشاهده پاسخ درست",
        disabled=selected == 0,
        key=f"check_{exam_id}_{question['number']}",
    ):
        correct = question.get("correct_answer")
        st.session_state.checked[question["number"]] = (selected == correct) if correct else None
        st.rerun()

if question["number"] in st.session_state.checked:
    correct = question.get("correct_answer")
    if correct is None:
        st.warning("این سؤال در کلید رسمی حذف شده است.")
    elif selected == correct:
        st.markdown(f'<div class="correct">✅ پاسخ درست است؛ گزینه {to_persian_digits(correct)}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="wrong">❌ پاسخ نادرست است؛ پاسخ صحیح گزینه {to_persian_digits(correct)}</div>', unsafe_allow_html=True)
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
if st.button("مشاهده نتایج"):
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
    st.session_state.result_summary = True
    st.rerun()

if st.session_state.get("result_summary"):
    graded = [q for q in questions if q.get("correct_answer") in {1, 2, 3, 4}]
    correct_count = sum(st.session_state.answers.get(q["number"], 0) == q["correct_answer"] for q in graded)
    wrong_count = sum(
        bool(st.session_state.answers.get(q["number"], 0))
        and st.session_state.answers.get(q["number"], 0) != q["correct_answer"]
        for q in graded
    )
    empty_count = len(graded) - correct_count - wrong_count
    percent = (3 * correct_count - wrong_count) / (3 * len(graded)) * 100 if graded else 0
    a, b, c, d = st.columns(4)
    a.metric("درست", to_persian_digits(correct_count))
    b.metric("غلط", to_persian_digits(wrong_count))
    c.metric("نزده", to_persian_digits(empty_count))
    d.metric("درصد کل ساده", f"{to_persian_digits(f'{percent:.2f}')}٪")

    is_electrical_exam = str(exam.get("exam_code")) == "1251" or "برق" in exam.get("title", "")
    if is_electrical_exam:
        st.markdown("### کارنامه درس‌ها")
        selected_code = st.selectbox(
            "کد ضریب / گرایش",
            list(ELECTRICAL_COEFFICIENT_CODES),
            key=f"coefficient_code_{exam_id}",
        )
        selected_subjects = list(ELECTRICAL_SUBJECTS)
        if selected_code.startswith("کد ضریب ۶"):
            final_subject = st.radio(
                "درس انتخابی کد ضریب ۶",
                ["الکترومغناطیس", BIOMEDICAL_SUBJECT],
                horizontal=True,
                key=f"coefficient_6_subject_{exam_id}",
            )
            selected_subjects[-1] = final_subject

        coefficients = ELECTRICAL_COEFFICIENT_CODES[selected_code]
        rows = []
        weighted_total = 0
        coefficient_total = 0
        for subject_name, coefficient in zip(selected_subjects, coefficients):
            result = calculate_subject_result(subject_name, questions, st.session_state.answers)
            rows.append({
                "درس": subject_name,
                "صحیح": to_persian_digits(result["correct"]),
                "غلط": to_persian_digits(result["wrong"]),
                "نزده": to_persian_digits(result["empty"]),
                "امتیاز خام": to_persian_digits(result["raw"]),
                "درصد": f"{to_persian_digits(f'{result['percent']:.2f}')}٪",
                "ضریب": to_persian_digits(coefficient),
            })
            if coefficient:
                weighted_total += result["percent"] * coefficient
                coefficient_total += coefficient
        weighted_score = weighted_total / coefficient_total if coefficient_total else 0
        st.table(rows)
        score_column, raw_column = st.columns(2)
        score_column.metric(
            "امتیاز وزنی کد ضریب",
            f"{to_persian_digits(f'{weighted_score:.2f}')} از ۱۰۰",
        )
        raw_column.metric("امتیاز خام پاسخ‌ها", to_persian_digits(3 * correct_count - wrong_count))
        st.caption("در هر درس، پاسخ صحیح ۳ امتیاز و پاسخ غلط ۱ امتیاز منفی دارد؛ سؤال نزده بدون امتیاز است.")
        st.info(
            "امتیاز نمایش‌داده‌شده بر پایه درصد درس‌ها و ضرایب رسمی محاسبه شده است، اما تراز یا رتبه رسمی نیست. "
            "تخمین رتبه پس از افزودن بانک کارنامه‌های تاریخی معتبر فعال می‌شود."
        )
