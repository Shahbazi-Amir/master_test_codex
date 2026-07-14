# آزمون ارشد مهندسی برق ۱۴۰۴

سامانه آزمون کارشناسی ارشد مهندسی برق، کد مجموعه `1251` و کد دفترچه `535C`.

## داده‌های موجود

- PDF رسمی ۳۷ صفحه‌ای سؤال‌ها و کلید سازمان سنجش
- ۱۲۵ رکورد سؤال با درس، شماره، چهار گزینه انتخابی و پاسخ صحیح
- ۱۲۵ تصویر PNG با نام‌های `question_001.png` تا `question_125.png`
- کلید رسمی در `data/answer_keys/key_1404.json`
- داده کامل آزمون در `data/questions/exam_1404.json`

هر تصویر سؤال، صفحه کامل رسمی مربوط به آن سؤال را نگه می‌دارد. این تصمیم عمدی است تا فرمول، نمودار، متن مشترک و گزینه‌ها ناقص بریده نشوند. چند سؤال واقع در یک صفحه، تصویر یکسان اما فایل مستقل دارند.

## ساختار

```text
assets/
├── source/arshad_bargh_1404_1251.pdf
└── questions/1404/question_001.png ... question_125.png
data/
├── answer_keys/key_1404.json
└── questions/exam_1404.json
master_exam_ui.py
requirements.txt
```

## اجرا

```bash
pip install -r requirements.txt
streamlit run master_exam_ui.py
```

## پاسخ‌های تشریحی

فیلدهای مربوط به پاسخ تشریحی از ابتدا در JSON تعریف شده‌اند:

- `explanation`
- `explanation_status`
- `explanation_sources`

در نسخه فعلی پاسخ تشریحی‌ها عمداً با وضعیت `pending_review` ثبت شده‌اند؛ هیچ توضیح تأییدنشده‌ای به‌عنوان پاسخ قطعی منتشر نشده است.
