#!/usr/bin/env python3
"""Build Computer Engineering (1277) exam assets from verified PDFs/pages."""

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAGE_RANGES = {
    1404: [(2,1,7),(3,8,12),(4,13,17),(5,18,20),(6,21,27),(7,28,31),(8,32,36),(9,37,40),(10,41,45),(11,46,50),(12,51,54),(13,55,59),(14,60,64),(15,65,67),(16,68,71),(17,72,74),(18,75,78),(19,79,83),(20,84,86),(21,87,90),(22,91,94),(23,95,100),(24,101,107),(25,108,112),(26,113,115)],
    1403: [(2,1,7),(3,8,10),(4,11,15),(5,16,20),(6,21,26),(7,27,32),(8,33,36),(9,37,41),(10,42,46),(11,47,52),(12,53,56),(13,57,60),(14,61,65),(15,66,70),(16,71,75),(17,76,77),(18,78,79),(19,80,80),(20,81,84),(21,85,88),(22,89,92),(23,93,95),(24,96,100),(25,101,104),(26,105,107),(27,108,112),(28,113,113),(29,114,115)],
    1402: [(2,1,7),(3,8,12),(4,13,17),(5,18,22),(6,23,29),(7,30,34),(8,35,38),(9,39,44),(10,45,49),(11,50,54),(12,55,59),(13,60,64),(14,65,69),(15,70,74),(16,75,78),(17,79,81),(18,82,82),(19,83,87),(20,88,90),(21,91,94),(22,95,98),(23,99,102),(24,103,105),(25,106,106),(26,107,108),(27,109,110),(28,111,112),(29,113,114),(30,115,115)],
}

KEYS = {
    1404: [4,1,3,2,3,4,2,3,1,2,3,4,2,3,1,4,1,2,2,4,3,2,1,3,1,4,2,1,1,4,3,3,2,1,3,3,4,1,2,3,1,2,2,4,1,3,2,3,1,3,1,3,4,1,2,3,4,1,4,2,2,1,3,2,4,3,2,4,1,3,3,3,1,2,2,2,3,2,1,4,3,4,2,3,1,3,4,2,1,4,2,3,2,4,1,3,1,4,4,1,2,2,3,2,4,3,1,4,4,1,1,2,1,3,4],
    1403: [2,4,1,3,3,4,1,2,2,1,2,1,4,2,3,1,3,2,3,4,1,3,4,2,2,3,4,1,1,2,4,3,3,4,2,4,4,2,1,4,1,4,1,2,3,None,3,1,3,2,1,2,4,2,3,3,4,4,1,3,2,4,2,4,1,3,4,4,2,2,1,2,1,3,2,3,3,2,1,3,1,4,2,2,1,3,4,2,3,2,3,1,3,4,1,3,3,1,4,2,4,2,1,3,4,4,2,3,3,4,1,4,3,None,2],
    1402: [4,1,3,2,2,4,1,3,3,1,4,1,3,4,2,3,1,1,4,4,2,1,3,4,4,2,2,2,2,2,1,2,1,3,4,2,3,2,1,4,1,3,2,4,3,4,1,4,1,2,1,4,2,3,4,3,2,2,1,3,2,4,3,1,3,4,4,4,4,2,1,1,3,2,2,3,2,1,2,4,2,4,1,3,4,2,1,4,2,3,1,4,2,3,2,2,1,2,4,1,4,3,2,3,2,4,1,4,1,2,4,3,3,4,2],
}

META = {
    1404: {"booklet_code": "335C", "duration_minutes": 250, "key_status": "official", "question_url": "https://cshub.ir/wp-content/uploads/2025/03/Q335C.pdf", "key_url": "https://cshub.ir/wp-content/uploads/2025/03/A335C.pdf"},
    1403: {"booklet_code": "164C", "duration_minutes": 240, "key_status": "final", "question_url": "https://cshub.ir/wp-content/uploads/2024/08/1403.pdf", "key_url": "https://cshub.ir/wp-content/uploads/2025/01/CE_1403_C_Final_Key.pdf"},
    1402: {"booklet_code": "934C", "duration_minutes": 240, "key_status": "initial_official", "question_url": "https://cshub.ir/wp-content/uploads/2024/08/1402.pdf", "key_url": "https://cshub.ir/wp-content/uploads/2025/01/CE_1402_C_Key.pdf"},
}

def subject(number):
    if number <= 25: return "زبان عمومی و تخصصی (انگلیسی)"
    if number <= 45: return "ریاضیات"
    if number <= 55: return "مجموعه دروس تخصصی ۱"
    if number <= 75: return "مجموعه دروس تخصصی ۲"
    if number <= 95: return "مجموعه دروس تخصصی ۳"
    return "مجموعه دروس تخصصی ۴"

def page_for(year, number):
    for page, start, end in PAGE_RANGES[year]:
        if start <= number <= end:
            return page
    raise ValueError((year, number))

def build(source_root):
    for year in (1402, 1403, 1404):
        assert len(KEYS[year]) == 115
        source_dir = ROOT / "assets/source/computer_engineering" / str(year)
        image_dir = ROOT / "assets/questions/computer_engineering" / str(year)
        question_data_dir = ROOT / "data/questions/computer_engineering"
        key_data_dir = ROOT / "data/answer_keys/computer_engineering"
        for directory in (source_dir, image_dir, question_data_dir, key_data_dir): directory.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_root / f"q{year}.pdf", source_dir / "questions.pdf")
        shutil.copy2(source_root / f"a{year}.pdf", source_dir / "answer_key.pdf")
        questions = []
        key_records = []
        for number, answer in enumerate(KEYS[year], 1):
            page = page_for(year, number)
            image_rel = Path("assets/questions/computer_engineering") / str(year) / f"question_{number:03}.png"
            shutil.copy2(source_root / "pages" / str(year) / f"page-{page:02}.png", ROOT / image_rel)
            status = "deleted" if answer is None else "official"
            key_records.append({"number": number, "correct_answer": answer, "status": status})
            questions.append({
                "number": number, "subject": subject(number), "image": image_rel.as_posix(),
                "source_page": page, "choices": [1,2,3,4], "correct_answer": answer,
                "answer_status": status, "explanation": None,
                "explanation_status": "not_applicable" if answer is None else "pending_review",
                "explanation_sources": [],
            })
        meta = META[year]
        exam = {
            "title": f"آزمون کارشناسی ارشد مهندسی کامپیوتر {year}", "field": "مهندسی کامپیوتر",
            "year": year, "exam_code": "1277", "booklet_code": meta["booklet_code"],
            "duration_minutes": meta["duration_minutes"], "total_questions": 115,
            "source": {"questions_pdf": f"assets/source/computer_engineering/{year}/questions.pdf", "answer_key_pdf": f"assets/source/computer_engineering/{year}/answer_key.pdf", "questions_url": meta["question_url"], "answer_key_url": meta["key_url"], "key_status": meta["key_status"]},
            "questions": questions,
        }
        key_doc = {"field": "مهندسی کامپیوتر", "year": year, "exam_code": "1277", "booklet_code": meta["booklet_code"], "key_status": meta["key_status"], "answers": key_records}
        (question_data_dir / f"exam_{year}.json").write_text(json.dumps(exam, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (key_data_dir / f"key_{year}.json").write_text(json.dumps(key_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    build(parser.parse_args().source_root)
