from pathlib import Path


def test_main_app_has_no_sample_questions():
    content = Path("master_exam_ui.py").read_text(encoding="utf-8")
    forbidden = ["در یک مدار مقاومتی ساده", "واحد توان ظاهری", "پایداری سیستم خطی"]
    for phrase in forbidden:
        assert phrase not in content


def test_main_app_requires_verified_extraction():
    content = Path("master_exam_ui.py").read_text(encoding="utf-8")
    assert "extracted_verified" in content
    assert "داده واقعی این سال هنوز وارد نشده است" in content


def test_sources_file_exists():
    assert Path("data/sources/electrical_1251_sources.json").exists()
