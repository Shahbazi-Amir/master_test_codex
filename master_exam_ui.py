import json
import time
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="آزمون ارشد برق ۱۲۵۱", page_icon="⚡", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"] { direction: rtl; text-align: right; }
.stButton button { width: 100%; }
.status-card {border:1px solid #ddd; border-radius:14px; padding:16px; margin:8px 0; background:#fafafa;}
.danger-card {border:1px solid #e0b4b4; border-radius:14px; padding:16px; margin:8px 0; background:#fff6f6;}
.timer-box {position:fixed;top:.7rem;left:1rem;z-index:9999;background:#111827;color:#fff;padding:.55rem .9rem;border-radius:.8rem;font-size:1.05rem;font-weight:700;direction:ltr;text-align:center;box-shadow:0 4px 18px rgba(0,0,0,.18);}
</style>
""", unsafe_allow_html=True)

APP_ROOT = Path(__file__).parent
SOURCES_PATH = APP_ROOT / "data" / "sources" / "electrical_1251_sources.json"
ANSWER_KEYS_DIR = APP_ROOT / "data" / "answer_keys"
EXAM_DURATION_SECONDS = 4 * 60 * 60
YEARS = list(range(1404, 1395, -1))


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback


def load_sources() -> list[dict]:
    payload = read_json(SOURCES_PATH, {})
    return payload.get("years", []) if isinstance(payload, dict) else []


def load_answer_key(year: int) -> dict | None:
    payload = read_json(ANSWER_KEYS_DIR / f"key_{year}.json", None)
    if not isinstance(payload, dict) or payload.get("exam_code") != "1251":
        return None
    items = []
    for item in payload.get("answers", []):
        try:
            qn = int(item["question_number"])
            opt = int(item["correct_option"])
        except (KeyError, TypeError, ValueError):
            continue
        if qn > 0 and opt in {1, 2, 3, 4}:
            items.append({"question_number": qn, "correct_option": opt, "lesson": item.get("lesson", "دروس اختصاصی")})
    payload["answers"] = sorted(items, key=lambda x: x["question_number"])
    payload["total_questions"] = len(items)
    return payload


def fmt(seconds: int) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds//3600:02d}:{(seconds%3600)//60:02d}:{seconds%60:02d}"


def score(user_answers: dict[int, int], key_items: list[dict]) -> dict:
    correct = wrong = empty = 0
    rows = []
    for item in key_items:
        qn = int(item["question_number"])
        true = int(item["correct_option"])
        user = int(user_answers.get(qn, 0) or 0)
        if user == 0:
            status, icon = "نزده", "⚪"
            empty += 1
        elif user == true:
            status, icon = "درست", "🟢"
            correct += 1
        else:
            status, icon = "غلط", "🔴"
            wrong += 1
        rows.append({"شماره سؤال": qn, "درس": item.get("lesson", "دروس اختصاصی"), "پاسخ شما": "نزده" if user == 0 else user, "پاسخ صحیح": true, "وضعیت": f"{icon} {status}"})
    total = len(key_items)
    return {"total": total, "correct": correct, "wrong": wrong, "empty": empty, "raw_percent": (correct / total * 100) if total else 0, "negative_percent": ((correct - wrong / 3) / total * 100) if total else 0, "rows": rows}


def reset(year: int):
    st.session_state.exam_year = year
    st.session_state.exam_started = False
    st.session_state.exam_finished = False
    st.session_state.started_at = None
    st.session_state.answers = {}


def start(year: int):
    st.session_state.exam_year = year
    st.session_state.exam_started = True
    st.session_state.exam_finished = False
    st.session_state.started_at = time.time()
    st.session_state.answers = {}


def timer_widget(remaining_seconds: int):
    st.markdown(f"<div class='timer-box' id='timerBox'>{fmt(remaining_seconds)}</div>", unsafe_allow_html=True)
    components.html(f"""
    <script>
    let remaining={int(max(0, remaining_seconds))};
    function pad(n){{return String(n).padStart(2,'0')}}
    function render(){{
      const h=pad(Math.floor(remaining/3600));
      const m=pad(Math.floor((remaining%3600)/60));
      const s=pad(remaining%60);
      const box=window.parent.document.getElementById('timerBox');
      if(box) box.innerText=`${{h}}:${{m}}:${{s}}`;
      remaining=Math.max(0,remaining-1);
    }}
    render(); setInterval(render,1000); setTimeout(()=>window.parent.location.reload(),30000);
    </script>
    """, height=0)


if "exam_year" not in st.session_state:
    reset(1404)

sources = load_sources()
source_by_year = {x.get("year"): x for x in sources if isinstance(x, dict)}

st.title("سامانه شبیه‌ساز واقعی آزمون کارشناسی ارشد مهندسی برق")
st.caption("کد مجموعه ۱۲۵۱ | آزمون PDF-based با پاسخ‌برگ دیجیتال و کلید واقعی")

selected_year = st.sidebar.selectbox("سال آزمون", YEARS, index=0)
mode = st.sidebar.radio("بخش", ["آزمون", "مرور نتیجه", "گزارش داده‌ها"])

if st.session_state.exam_year != selected_year:
    reset(selected_year)

source = source_by_year.get(selected_year, {})
answer_key = load_answer_key(selected_year)
key_items = answer_key["answers"] if answer_key else []
total_questions = len(key_items)
question_pdf_url = source.get("question_pdf_url") or (answer_key or {}).get("question_pdf_url")
answer_key_pdf_url = source.get("answer_key_pdf_url") or (answer_key or {}).get("source_url")

st.sidebar.markdown("### وضعیت سال")
st.sidebar.write("PDF سؤال:", "✅" if question_pdf_url else "❌")
st.sidebar.write("کلید واقعی:", "✅" if total_questions else "❌")
st.sidebar.write("تعداد سؤال:", total_questions if total_questions else "نامشخص")
st.sidebar.write("حالت آزمون:", "فعال" if question_pdf_url and total_questions else "غیرفعال")

if mode == "گزارش داده‌ها":
    rows = []
    for year in YEARS:
        item = source_by_year.get(year, {})
        key = load_answer_key(year)
        rows.append({"سال": year, "PDF سؤال": "دارد" if item.get("question_pdf_url") else "ندارد", "PDF کلید": "دارد" if item.get("answer_key_pdf_url") else "ندارد", "تعداد پاسخ کلید": len(key["answers"]) if key else 0, "آزمون فعال": "بله" if item.get("question_pdf_url") and key else "خیر", "وضعیت": item.get("status", "incomplete")})
    st.subheader("گزارش داده‌ها")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.stop()

if mode == "مرور نتیجه" and not st.session_state.get("exam_finished"):
    st.warning("هنوز نتیجه‌ای برای مرور وجود ندارد. اول آزمون را شروع و پایان بده.")
    st.stop()

st.subheader(f"آزمون کارشناسی ارشد مهندسی برق ۱۲۵۱ - سال {selected_year}")

if not question_pdf_url or not total_questions:
    st.markdown("""
    <div class='danger-card'>
    <b>این سال هنوز آزمون نمره‌دار فعال ندارد.</b><br>
    برای فعال شدن آزمون باید هم PDF سؤال و هم کلید واقعی همان سال در مخزن ثبت شده باشد.
    </div>
    """, unsafe_allow_html=True)
    if source.get("notes"):
        st.info(source["notes"])
    st.stop()

elapsed = int(time.time() - st.session_state.started_at) if st.session_state.exam_started and st.session_state.started_at else 0
remaining = EXAM_DURATION_SECONDS - elapsed

if st.session_state.exam_started and not st.session_state.exam_finished:
    timer_widget(remaining)
    if remaining <= 0:
        st.session_state.exam_finished = True
        st.warning("زمان آزمون تمام شد؛ نتیجه ثبت شد.")
        st.rerun()
else:
    st.markdown("<div class='timer-box'>04:00:00</div>", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("تعداد سؤال", total_questions)
c2.metric("مدت آزمون", "۴ ساعت")
c3.metric("کد مجموعه", "۱۲۵۱")
c4.metric("وضعیت", "فعال")

st.markdown("### دفترچه سؤال")
st.markdown(f"[مشاهده/دانلود PDF سؤال]({question_pdf_url})")
if answer_key_pdf_url:
    st.markdown(f"[مشاهده PDF کلید منبع]({answer_key_pdf_url})")

with st.expander("نمایش PDF سؤال داخل صفحه", expanded=True):
    st.markdown(f"<iframe src='{question_pdf_url}' width='100%' height='650px' style='border:1px solid #ddd;border-radius:12px;'></iframe>", unsafe_allow_html=True)
    st.caption("اگر PDF داخل صفحه باز نشد، از لینک دانلود بالا استفاده کن.")

if not st.session_state.exam_started:
    st.info("برای شروع پاسخ‌برگ و تایمر، دکمه زیر را بزن.")
    if st.button("شروع آزمون"):
        start(selected_year)
        st.rerun()
    st.stop()

if not st.session_state.exam_finished:
    st.markdown("### پاسخ‌برگ دیجیتال")
    st.caption("برای هر سؤال گزینه ۱ تا ۴ را بزن؛ گزینه «نزده» یعنی بدون پاسخ.")
    options = ["نزده", "1", "2", "3", "4"]
    cols = st.columns(5)
    for idx, item in enumerate(key_items):
        qn = int(item["question_number"])
        with cols[idx % 5]:
            selected = st.radio(f"سؤال {qn}", options, index=int(st.session_state.answers.get(qn, 0)), key=f"ans_{selected_year}_{qn}", horizontal=True)
            st.session_state.answers[qn] = 0 if selected == "نزده" else int(selected)
    st.divider()
    if st.button("پایان آزمون و مشاهده نتیجه"):
        st.session_state.exam_finished = True
        st.rerun()
else:
    result = score(st.session_state.answers, key_items)
    st.markdown("## نتیجه آزمون")
    r1, r2, r3, r4, r5, r6 = st.columns(6)
    r1.metric("کل سؤال‌ها", result["total"])
    r2.metric("درست", result["correct"])
    r3.metric("غلط", result["wrong"])
    r4.metric("نزده", result["empty"])
    r5.metric("درصد خام", f"{result['raw_percent']:.2f}%")
    r6.metric("درصد با نمره منفی", f"{result['negative_percent']:.2f}%")
    st.dataframe(pd.DataFrame(result["rows"]), use_container_width=True, hide_index=True)
    st.markdown("### پاسخ و توضیح سؤال‌ها")
    for row in result["rows"]:
        qn = int(row["شماره سؤال"])
        with st.expander(f"پاسخ و توضیح سؤال {qn} - {row['وضعیت']}"):
            st.write("پاسخ شما:", row["پاسخ شما"])
            st.write("پاسخ صحیح:", row["پاسخ صحیح"])
            st.write("وضعیت:", row["وضعیت"])
            st.info("توضیح تشریحی معتبر هنوز وارد نشده است.")
    st.warning("تخمین قبولی فعلاً غیرقطعی است و باید با داده واقعی کارنامه‌ها و ظرفیت‌ها تکمیل شود.")
    if result["negative_percent"] >= 60:
        st.success("برآورد خیلی کلی: وضعیت خوب؛ اما قبولی نهایی به گرایش، سهمیه، ظرفیت و رتبه واقعی وابسته است.")
    elif result["negative_percent"] >= 40:
        st.info("برآورد خیلی کلی: وضعیت متوسط؛ برای تخمین دقیق باید کارنامه‌های واقعی اضافه شود.")
    else:
        st.error("برآورد خیلی کلی: شانس محدود؛ نیاز به تحلیل دقیق‌تر و داده واقعی قبولی دارد.")
    if st.button("شروع دوباره"):
        reset(selected_year)
        st.rerun()
