import streamlit as st
import pandas as pd

st.set_page_config(page_title="آزمون ارشد برق", page_icon="⚡", layout="wide")

st.markdown(
    """
    <style>
    html, body, [class*="css"] { direction: rtl; text-align: right; }
    .stButton button { width: 100%; }
    .exam-card {border:1px solid #ddd; border-radius:12px; padding:16px; margin:8px 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

QUESTIONS = [
    {
        "year": 1404,
        "lesson": "مدارهای الکتریکی",
        "question": "در یک مدار مقاومتی ساده، اگر ولتاژ دو برابر شود و مقاومت ثابت بماند، جریان چه تغییری می‌کند؟",
        "options": ["نصف می‌شود", "دو برابر می‌شود", "ثابت می‌ماند", "صفر می‌شود"],
        "answer": 1,
        "explanation": "طبق قانون اهم I = V/R است؛ با ثابت بودن R، جریان متناسب با ولتاژ تغییر می‌کند.",
    },
    {
        "year": 1404,
        "lesson": "ماشین‌های الکتریکی",
        "question": "واحد توان ظاهری در مدارهای AC چیست؟",
        "options": ["وات", "ولت‌آمپر", "اهم", "فاراد"],
        "answer": 1,
        "explanation": "توان ظاهری با واحد VA یا ولت‌آمپر بیان می‌شود.",
    },
    {
        "year": 1403,
        "lesson": "کنترل خطی",
        "question": "پایداری سیستم خطی معمولاً با کدام مفهوم بررسی می‌شود؟",
        "options": ["ریشه‌های معادله مشخصه", "مقدار مقاومت", "ظرفیت خازن", "توان نامی"],
        "answer": 0,
        "explanation": "مکان قطب‌ها یا ریشه‌های معادله مشخصه نقش اصلی در پایداری سیستم دارد.",
    },
]

if "answers" not in st.session_state:
    st.session_state.answers = {}
if "finished" not in st.session_state:
    st.session_state.finished = False

st.title("سامانه آزمون کارشناسی ارشد مهندسی برق")
st.caption("نسخه اولیه قابل اجرا؛ داده‌های فعلی نمونه هستند و باید با داده واقعی جایگزین شوند.")

years = sorted({q["year"] for q in QUESTIONS}, reverse=True)
selected_year = st.sidebar.selectbox("سال آزمون", years)
mode = st.sidebar.radio("حالت", ["آزمون", "مرور نتیجه"])
filtered = [q for q in QUESTIONS if q["year"] == selected_year]

if mode == "آزمون" and not st.session_state.finished:
    st.subheader(f"آزمون سال {selected_year}")
    for i, q in enumerate(filtered):
        st.markdown(f"<div class='exam-card'><b>سؤال {i+1} - {q['lesson']}</b><br>{q['question']}</div>", unsafe_allow_html=True)
        choice = st.radio(
            "گزینه را انتخاب کنید",
            q["options"],
            key=f"q_{selected_year}_{i}",
            index=None,
        )
        if choice is not None:
            st.session_state.answers[(selected_year, i)] = q["options"].index(choice)
        st.divider()

    if st.button("پایان آزمون و مشاهده نتیجه"):
        st.session_state.finished = True
        st.rerun()

else:
    st.subheader(f"نتیجه آزمون سال {selected_year}")
    rows = []
    correct = wrong = empty = 0
    for i, q in enumerate(filtered):
        user_answer = st.session_state.answers.get((selected_year, i))
        if user_answer is None:
            status = "بدون پاسخ"
            empty += 1
        elif user_answer == q["answer"]:
            status = "درست"
            correct += 1
        else:
            status = "غلط"
            wrong += 1
        rows.append({"شماره": i + 1, "درس": q["lesson"], "وضعیت": status})

    total = len(filtered)
    raw_percent = ((correct - wrong / 3) / total * 100) if total else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("درست", correct)
    c2.metric("غلط", wrong)
    c3.metric("بدون پاسخ", empty)
    c4.metric("درصد با نمره منفی", f"{raw_percent:.1f}%")

    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    st.subheader("مرور سؤال‌ها")
    for i, q in enumerate(filtered):
        user_answer = st.session_state.answers.get((selected_year, i))
        is_correct = user_answer == q["answer"]
        if user_answer is None:
            color = "⚪"
            result = "بدون پاسخ"
        elif is_correct:
            color = "🟢"
            result = "درست"
        else:
            color = "🔴"
            result = "غلط"

        with st.expander(f"{color} سؤال {i+1} - {result}"):
            st.write(q["question"])
            st.write("گزینه صحیح:", q["options"][q["answer"]])
            if user_answer is not None:
                st.write("پاسخ شما:", q["options"][user_answer])
            st.info(q["explanation"])

    st.warning("رتبه و قبولی در این نسخه فقط نمونه/تخمینی است و داده واقعی سنجش هنوز وارد نشده است.")
    st.write("رتبه تخمینی نمونه: ۸۰۰ تا ۱۲۰۰")
    st.write("شانس قبولی نمونه: متوسط در برخی گرایش‌ها")

    if st.button("شروع دوباره"):
        st.session_state.answers = {}
        st.session_state.finished = False
        st.rerun()
