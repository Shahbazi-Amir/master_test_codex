#!/usr/bin/env python3
"""Build the 1405 Computer Engineering exam and apply both official answer keys."""

import csv
import io
import json
import math
import re
import shutil
import subprocess
import tempfile
import traceback
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "data/diagnostics/1405_new_sources"
STATUS_PATH = DIAG / "build_status.json"
DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

COMPUTER_PDF = ROOT / "assets/source/arshad_computer_1405.pdf"
COMPUTER_KEY_PDF = ROOT / "assets/source/answer_key_computer_1405.pdf"
ELECTRICAL_KEY_PDF = ROOT / "assets/source/answer_key_electrical_1405.pdf"
ELECTRICAL_EXAM = ROOT / "data/questions/exam_1405.json"

PAGE_RANGES = [
    (2, 1, 10), (3, 11, 15), (4, 16, 20), (5, 21, 25),
    (6, 26, 30), (7, 31, 34), (8, 35, 38), (9, 39, 43),
    (10, 44, 47), (11, 48, 52), (12, 53, 57), (13, 58, 63),
    (14, 64, 68), (15, 69, 75), (16, 76, 78), (17, 79, 80),
    (18, 81, 84), (19, 85, 88), (20, 89, 91), (21, 92, 95),
    (22, 96, 99), (23, 100, 103), (24, 104, 106), (25, 107, 111),
    (26, 112, 115),
]

COMPUTER_KEY_MANUAL = [
    2,1,3,1,4,4,2,3,1,3,4,1,3,1,1,4,3,1,3,3,4,3,1,4,3,3,1,3,3,3,1,4,1,3,4,1,4,3,4,1,
    4,3,3,1,2,1,3,1,4,2,3,4,3,1,3,4,3,1,4,2,3,1,3,4,1,3,3,3,1,4,3,3,3,4,2,1,3,3,3,4,
    1,4,1,3,2,3,4,3,1,2,4,1,4,3,3,3,4,3,1,1,4,3,3,1,2,4,1,2,4,2,1,3,4,1,4,
]


def subject(number: int) -> str:
    if number <= 25:
        return "زبان عمومی و تخصصی (انگلیسی)"
    if number <= 45:
        return "ریاضیات"
    if number <= 55:
        return "مجموعه دروس تخصصی ۱ (نظریه زبان‌ها و ماشین‌ها، سیگنال‌ها و سیستم‌ها)"
    if number <= 75:
        return "مجموعه دروس تخصصی ۲ (ساختمان داده‌ها، طراحی الگوریتم و هوش مصنوعی)"
    if number <= 95:
        return "مجموعه دروس تخصصی ۳ (مدار منطقی، معماری کامپیوتر و الکترونیک دیجیتال)"
    return "مجموعه دروس تخصصی ۴ (سیستم‌های عامل، شبکه‌های کامپیوتری و پایگاه داده‌ها)"


def page_for(number: int) -> int:
    for page, first, last in PAGE_RANGES:
        if first <= number <= last:
            return page
    raise ValueError(number)


def render_page(pdf: Path, page: int, output: Path, dpi: int = 200) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    prefix = output.with_suffix("")
    subprocess.run([
        "pdftoppm", "-f", str(page), "-l", str(page), "-r", str(dpi), "-png",
        str(pdf), str(prefix),
    ], check=True)
    candidates = sorted(output.parent.glob(prefix.name + "-*.png")) or [output]
    generated = next((path for path in candidates if path.exists()), None)
    if generated is None:
        raise RuntimeError(f"Failed to render page {page}")
    if generated != output:
        generated.replace(output)
    return output


def find_white_cut(image: Image.Image, target: int, low: int, high: int) -> int:
    gray = ImageOps.grayscale(image)
    width, height = gray.size
    pixels = gray.load()
    low = max(0, low)
    high = min(height - 1, high)
    best_y = max(low, min(target, high))
    best_score = float("inf")
    for y in range(low, high + 1):
        score = 0
        for yy in range(max(0, y - 5), min(height, y + 6)):
            dark = sum(1 for x in range(50, max(51, width - 50), 4) if pixels[x, yy] < 210)
            score += dark
        distance_penalty = abs(y - target) * 0.05
        value = score + distance_penalty
        if value < best_score:
            best_score = value
            best_y = y
    return best_y


def build_group_crops(temp: Path) -> dict[int, str]:
    image_dir = ROOT / "assets/questions/computer_engineering/1405"
    image_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for page, first, last in PAGE_RANGES:
        if last <= 25:
            continue
        rendered = render_page(COMPUTER_PDF, page, temp / f"page-{page:02d}.png")
        image = Image.open(rendered).convert("RGB")
        width, height = image.size
        top, bottom = int(height * 0.055), int(height * 0.965)
        numbers = list(range(first, last + 1))
        groups = [numbers[index:index + 3] for index in range(0, len(numbers), 3)]
        cuts = [top]
        consumed = 0
        for group in groups[:-1]:
            consumed += len(group)
            target = top + round((bottom - top) * consumed / len(numbers))
            span = max(70, round((bottom - top) * 0.11))
            cuts.append(find_white_cut(image, target, target - span, target + span))
        cuts.append(bottom)
        for index, group in enumerate(groups):
            y1 = max(top, cuts[index] - 30)
            y2 = min(bottom, cuts[index + 1] + 30)
            crop = image.crop((int(width * 0.025), y1, int(width * 0.975), y2))
            for number in group:
                relative = Path("assets/questions/computer_engineering/1405") / f"question_{number:03d}.png"
                crop.save(ROOT / relative, format="PNG", optimize=True)
                result[number] = relative.as_posix()
    return result


def clean_english(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def language_questions() -> dict[int, dict]:
    cloze = clean_english(
        "Cognitive psychology focuses on how people perceive, store, and interpret information, "
        "________ (8) processes like perception, reasoning, and problem solving. ________ (9) "
        "behaviorists, cognitive psychologists believe it is necessary to look at internal mental "
        "processes in order to understand behavior. Cognitive psychology has been extremely "
        "influential, and much contemporary research ________ (10)."
    )
    passage1 = clean_english(
        "Based on exponentially increasing computing power and big data availability, artificial "
        "intelligence (AI) has gained substantial traction in recent years. In 2016, AlphaGo, a deep "
        "reinforcement learning algorithm developed by Google, was able to beat Lee Sedol, arguably "
        "one of the most renowned players of the board game ‘Go’, which is considered to be multiple "
        "times more complex than chess. With the introduction of ChatGPT, AI has made its way to a "
        "broad common perception, raising promising expectations about impactful AI use cases in "
        "business research and practice. Although AI-related literature is rich, we currently lack a "
        "comprehensive understanding of the use of AI algorithms. The absence of a concise AI "
        "definition and taxonomy in business results in a dispersed knowledge base, which has two "
        "critical implications. First, it currently seems challenging to assess the extent to which "
        "management research has exploited the potential of AI algorithms. Second, an overview of "
        "current trends as well as future potentials of applied AI remains vague."
    )
    passage2 = clean_english(
        "The operating system (OS) operates and controls the various units of a computer, managing "
        "how software uses hardware to ensure the computer functions as intended in a systematic, "
        "reliable, and efficient manner. The kernel, the controlling part of the OS, remains in the "
        "main storage permanently during the computer’s operation. Principal functions of an OS "
        "include scheduling and loading programs, controlling hardware resources, protecting "
        "hardware, software, and data from improper use, loading programs and functions into main "
        "storage as required, passing control from one job to another under priority systems, "
        "providing error correction routines, maintaining a complete record of all process "
        "activities, and communicating with the computer operator. Operating systems have evolved "
        "over time, driven by hardware advancements and application needs. Initially, computers "
        "were programmed directly with machine instructions or assembly code, with no controls over "
        "system use. The first OS challenge was to enable transitioning from one job to another "
        "without stopping the machine, entering a new program, and restarting. The batch operating "
        "system concept provided a solution by allowing operators to load several jobs at once, "
        "which the system then executed sequentially, taking control between jobs to set up hardware "
        "and release control to the next job."
    )
    passage3 = clean_english(
        "Named after mathematician and computer scientist John von Neumann, the Von Neumann "
        "architecture features a single memory space for both data and instructions, which are "
        "fetched and executed sequentially. This means that programs and data are stored in the same "
        "memory, allowing for flexible and easy modification of programs. But instructions are also "
        "fetched and executed one at a time, which creates a bottleneck where the CPU cannot fetch "
        "instructions and data simultaneously. [1] This is known as the Von Neumann bottleneck. To "
        "address this, modern CPUs employ techniques like caching and pipelining to improve "
        "efficiency. Still, the Von Neumann architecture remains highly relevant and influential in "
        "computer design. [2] Von Neumann’s architecture introduced the concept of stored-program "
        "computers, where both instructions and data are stored in the same memory, allowing for "
        "flexible program execution. Unlike the Von Neumann architecture where instructions and data "
        "share the same memory and data paths, Harvard architecture is a type of computer "
        "architecture that has separate storage units and dedicated pathways for instructions and "
        "data. [3] By having separate pathways, the CPU can fetch instructions and access data at the "
        "same time, without waiting for each other, leading to faster program execution, especially "
        "for tasks that involve a lot of data movement. Separate memory units can be optimized for "
        "their specific purposes. For example, instruction memory might be read-only, while data "
        "memory might be optimized for fast read/write operations. Still, implementing separate "
        "storage and pathways can be more complex than the simpler Von Neumann architecture and "
        "having separate memory units can increase the overall cost of the system. [4]"
    )
    data = {
        1: ("His words should be understood in ______ in order to be correctly interpreted.", ["direction", "context", "expert", "interest"]),
        2: ("She told her friends about her intention to go abroad, changing her first decision to keep it ______.", ["secret", "familiar", "final", "positive"]),
        3: ("She has ______ in her library the complete works of many Persian poets such as Hafez, Mowlana, Sa’di, Nezami and Ferdowsi.", ["defended", "arrived", "collected", "caused"]),
        4: ("A defining ______ of online art is that it can be seen anywhere by anyone with an Internet-connected computer.", ["characteristic", "inspiration", "spectator", "artifact"]),
        5: ("For decades, the hygiene hypothesis has posited that the germs we are exposed to in early childhood can ______ us from developing allergies.", ["desist", "prescribe", "cease", "prevent"]),
        6: ("I was in need of money and not at all ______ about experiments, so I concurred and received the new medicine at the local hospital.", ["affluent", "plausible", "respective", "apprehensive"]),
        7: ("Some people suffer from a chronic case of rabid chauvinism; they brandish the banners and shields of their own tribe and ______ those of the others.", ["exculpate", "excoriate", "extrapolate", "expatiate"]),
        8: ("Choose the best option for blank (8).", ["that studies", "studies", "studying", "and study"], cloze),
        9: ("Choose the best option for blank (9).", ["Unlike", "Although", "However", "Even"], cloze),
        10: ("Choose the best option for blank (10).", ["is cognitive with nature", "being in cognitive nature", "is cognitive in nature", "being naturally cognitive"], cloze),
        11: ("The word ‘substantial’ in paragraph 1 is closest in meaning to ______.", ["minimal", "new", "original", "significant"], passage1),
        12: ("The word ‘its’ in paragraph 1 refers to ______.", ["AI", "ChatGPT", "introduction", "way"], passage1),
        13: ("According to paragraph 1, which statement is true about the game known as ‘Go’?", ["It was first created by AlphaGo.", "It was developed by Google.", "AI is good at playing it.", "It is simpler than chess."], passage1),
        14: ("All of the following words are mentioned in the passage EXCEPT ______.", ["circuit", "dispersed", "exponentially", "reinforcement"], passage1),
        15: ("According to the passage, which statement is true?", ["It is difficult now to evaluate how much management research has employed the potentials offered by AI algorithms.", "Our understanding of the use of AI algorithms is currently limited, primarily because of a lack of AI-related literature.", "Current evaluations show that there are no optimistic prospects regarding the application of AI in business research.", "A comprehensive overview of present trends and future possibilities in applied AI is currently made available."], passage1),
        16: ("The word ‘improper’ in paragraph 1 is closest in meaning to ______.", ["potential", "peripheral", "consequent", "inappropriate"], passage2),
        17: ("Which option best describes the function of paragraph 2?", ["It explains a fact which in a way undermines the main argument of the previous paragraph.", "It elaborates on the potential of a computer system to pave the way for future advancements.", "It refers to the historical development of a computer system mentioned in paragraph 1.", "It demonstrates the initial steps taken for the manufacturing of computer hardware."], passage2),
        18: ("Which technique is used in the passage?", ["Cause and effect", "Irony", "Direct quotation", "Statistics"], passage2),
        19: ("The passage provides sufficient information to answer which question(s)? I. In which country was the first computer introduced? II. What is the name of the most common error in computer systems? III. What was among the first problems operating systems needed to solve?", ["I and II", "I and III", "Only III", "Only II"], passage2),
        20: ("Which option best describes the overall tone of the passage?", ["Passionate", "Objective", "Humorous", "Ambivalent"], passage2),
        21: ("Which option is NOT mentioned with reference to the Von Neumann architecture in paragraph 1?", ["A limitation observed in its function", "A development associated with it", "One of the features that it enjoys", "The century when it was designed"], passage3),
        22: ("Which option best expresses the writer’s opinion about dedicated pathways for instructions and data in Harvard architecture?", ["He completely confirms this solution unequivocally.", "He acknowledges its efficacy with some reservations.", "He rejects its suitability entirely.", "He remains silent on this point."], passage3),
        23: ("What does the passage mainly discuss?", ["Two different computer architectures", "The function of memory in computers", "Von Neumann’s role in the development of computers", "The influence of mathematics on computer technology"], passage3),
        24: ("According to the passage, which statement is true?", ["Harvard architecture is widely regarded as more cost-effective than alternative designs.", "In Von Neumann architecture, instructions and data are stored in separate memory spaces.", "Von Neumann architecture is no longer relevant because of modern alternatives.", "In Harvard architecture, the CPU can simultaneously fetch instructions and access data."], passage3),
        25: ("At which position [1], [2], [3], or [4] can this sentence best be inserted: ‘This allows for simultaneous access to instructions and data, potentially improving performance.’", ["[1]", "[2]", "[3]", "[4]"], passage3),
    }
    result = {}
    for number, item in data.items():
        text, choices, *context = item
        result[number] = {"text": text, "choice_texts": choices}
        if context:
            result[number]["context"] = context[0]
    return result


def normalize_token(text: str) -> str:
    return text.translate(DIGITS).replace("|", "1").strip()


def render_key(pdf: Path, target: Path) -> Path:
    prefix = target.with_suffix("")
    subprocess.run(["pdftoppm", "-f", "1", "-l", "1", "-r", "400", "-gray", "-png", str(pdf), str(prefix)], check=True)
    candidates = sorted(target.parent.glob(prefix.name + "-*.png")) or [target]
    generated = next((path for path in candidates if path.exists()), None)
    if generated is None:
        raise RuntimeError("key render failed")
    if generated != target:
        generated.replace(target)
    return target


def numeric_tokens(image: Path) -> list[dict]:
    tsv = subprocess.check_output(["tesseract", str(image), "stdout", "-l", "fas+eng", "--psm", "6", "tsv"], text=True, errors="replace")
    output = []
    for row in csv.DictReader(io.StringIO(tsv), delimiter="\t"):
        raw = row.get("text", "").strip()
        if row.get("level") != "5" or not raw:
            continue
        cleaned = re.sub(r"\D", "", normalize_token(raw))
        if not cleaned or len(cleaned) > 3:
            continue
        value = int(cleaned)
        if not 1 <= value <= 140:
            continue
        output.append({"value": value, "x": int(row["left"]) + int(row["width"]) / 2, "y": int(row["top"]) + int(row["height"]) / 2, "conf": float(row["conf"])})
    return output


def cluster_values(values: list[float], tolerance: float) -> list[list[int]]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    clusters = []
    for index in order:
        if not clusters or abs(values[index] - sum(values[i] for i in clusters[-1]) / len(clusters[-1])) > tolerance:
            clusters.append([index])
        else:
            clusters[-1].append(index)
    return clusters


def parse_key_table(pdf: Path, groups: list[tuple[int, int]], temp: Path, label: str) -> list[int]:
    image_path = render_key(pdf, temp / f"{label}-key.png")
    tokens = numeric_tokens(image_path)
    y_clusters = cluster_values([token["y"] for token in tokens], 30)
    rows = []
    for cluster in y_clusters:
        row = [tokens[index] for index in cluster]
        if len(row) >= len(groups) + 1 and any(token["value"] > 4 for token in row):
            rows.append(sorted(row, key=lambda token: token["x"]))
    if len(rows) < 38:
        raise RuntimeError(f"Only {len(rows)} key rows detected for {label}")
    if len(rows) > 40:
        best = None
        for start in range(len(rows) - 39):
            window = rows[start:start + 40]
            centers = [sum(token["y"] for token in row) / len(row) for row in window]
            gaps = [centers[i + 1] - centers[i] for i in range(39)]
            score = max(gaps) - min(gaps)
            if best is None or score < best[0]:
                best = (score, window)
        rows = best[1]
    elif len(rows) == 39:
        centers = [sum(token["y"] for token in row) / len(row) for row in rows]
        gaps = [centers[i + 1] - centers[i] for i in range(len(centers) - 1)]
        missing = max(range(len(gaps)), key=lambda index: gaps[index]) + 1
        rows.insert(missing, [])
    rows = rows[:40]

    all_tokens = [token for row in rows for token in row]
    x_values = [token["x"] for token in all_tokens]
    # Quantile-initialized one-dimensional k-means for question/answer columns.
    column_count = len(groups) * 2
    centers = [sorted(x_values)[round((i + 0.5) * (len(x_values) - 1) / column_count)] for i in range(column_count)]
    for _ in range(30):
        assigned = [[] for _ in centers]
        for value in x_values:
            index = min(range(len(centers)), key=lambda i: abs(value - centers[i]))
            assigned[index].append(value)
        new = [sum(bucket) / len(bucket) if bucket else centers[i] for i, bucket in enumerate(assigned)]
        if max(abs(a - b) for a, b in zip(centers, new)) < 0.1:
            break
        centers = new
    centers.sort()

    column_tokens = [[] for _ in centers]
    for token in all_tokens:
        index = min(range(len(centers)), key=lambda i: abs(token["x"] - centers[i]))
        column_tokens[index].append(token["value"])
    pairs = []
    for index in range(0, len(centers), 2):
        pair_indices = [index, index + 1]
        question_index = max(pair_indices, key=lambda i: sum(value > 4 for value in column_tokens[i]))
        answer_index = pair_indices[0] if pair_indices[1] == question_index else pair_indices[1]
        question_values = [value for value in column_tokens[question_index] if value > 4]
        median = sorted(question_values)[len(question_values) // 2] if question_values else 0
        pairs.append({"q": question_index, "a": answer_index, "median": median})
    pairs.sort(key=lambda pair: pair["median"])
    if len(pairs) != len(groups):
        raise RuntimeError("key column pairing failed")

    image = Image.open(image_path).convert("L")
    row_centers = []
    for row in rows:
        row_centers.append(sum(token["y"] for token in row) / len(row) if row else None)
    known = [(i, value) for i, value in enumerate(row_centers) if value is not None]
    if len(known) < 2:
        raise RuntimeError("not enough key rows")
    first_i, first_y = known[0]
    last_i, last_y = known[-1]
    step = (last_y - first_y) / (last_i - first_i)
    row_centers = [value if value is not None else first_y + (i - first_i) * step for i, value in enumerate(row_centers)]

    def cell_answer(row_index: int, answer_column: int) -> int:
        row = rows[row_index]
        candidates = []
        for token in row:
            nearest = min(range(len(centers)), key=lambda i: abs(token["x"] - centers[i]))
            if nearest == answer_column and 1 <= token["value"] <= 4:
                candidates.append(token)
        if candidates:
            return max(candidates, key=lambda token: token["conf"])["value"]
        x = centers[answer_column]
        x_gap = min(abs(x - other) for other in centers if other != x)
        y = row_centers[row_index]
        y1 = (row_centers[row_index - 1] + y) / 2 if row_index else y - step / 2
        y2 = (row_centers[row_index + 1] + y) / 2 if row_index < 39 else y + step / 2
        crop = image.crop((max(0, int(x - x_gap * 0.38)), max(0, int(y1)), min(image.width, int(x + x_gap * 0.38)), min(image.height, int(y2))))
        crop = ImageOps.autocontrast(crop.resize((crop.width * 4, crop.height * 4)))
        attempts = []
        for threshold in (120, 150, 180, 210):
            binary = crop.point(lambda pixel, t=threshold: 255 if pixel > t else 0)
            with tempfile.NamedTemporaryFile(suffix=".png") as handle:
                binary.save(handle.name)
                text = subprocess.check_output(["tesseract", handle.name, "stdout", "--psm", "10", "-c", "tessedit_char_whitelist=1234۱۲۳۴١٢٣٤"], text=True, errors="replace")
            cleaned = re.sub(r"\D", "", normalize_token(text))
            if cleaned and int(cleaned[-1]) in {1, 2, 3, 4}:
                attempts.append(int(cleaned[-1]))
        if attempts:
            return max(set(attempts), key=attempts.count)
        raise RuntimeError(f"Missing answer cell {label}, row {row_index + 1}, column {answer_column}")

    answers = [None] * max(end for _, end in groups)
    for pair, (start, end) in zip(pairs, groups):
        for row_index, question_number in enumerate(range(start, end + 1)):
            answers[question_number - 1] = cell_answer(row_index, pair["a"])
    if any(value not in {1, 2, 3, 4} for value in answers):
        raise RuntimeError(f"Incomplete {label} key")
    (DIAG / f"parsed_{label}_key.json").write_text(json.dumps(answers, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return answers


def write_key(path: Path, field: str, code: str, booklet: str, answers: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "field": field,
        "year": 1405,
        "exam_code": code,
        "booklet_code": booklet,
        "key_status": "official",
        "answers": [{"number": number, "correct_answer": answer, "status": "official"} for number, answer in enumerate(answers, 1)],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build() -> dict:
    if len(COMPUTER_KEY_MANUAL) != 115:
        raise RuntimeError("manual computer key length")
    with tempfile.TemporaryDirectory(prefix="build-1405-") as temp_name:
        temp = Path(temp_name)
        scanned_computer = parse_key_table(COMPUTER_KEY_PDF, [(1, 40), (41, 80), (81, 115)], temp, "computer")
        electrical_answers = parse_key_table(ELECTRICAL_KEY_PDF, [(1, 40), (41, 80), (81, 120), (121, 140)], temp, "electrical")
        mismatches = [index + 1 for index, (a, b) in enumerate(zip(scanned_computer, COMPUTER_KEY_MANUAL)) if a != b]
        if mismatches:
            raise RuntimeError(f"Computer key OCR/manual mismatch at {mismatches}")
        images = build_group_crops(temp)

    language = language_questions()
    questions = []
    for number, answer in enumerate(COMPUTER_KEY_MANUAL, 1):
        record = {
            "number": number,
            "subject": subject(number),
            "source_page": page_for(number),
            "choices": [1, 2, 3, 4],
            "correct_answer": answer,
            "answer_status": "official",
            "explanation": None,
            "explanation_status": "pending_review",
            "explanation_sources": [],
        }
        if number <= 25:
            record.update(language[number])
        else:
            record["image"] = images[number]
        questions.append(record)

    computer_exam = {
        "title": "آزمون کارشناسی ارشد مهندسی کامپیوتر ۱۴۰۵",
        "field": "مهندسی کامپیوتر",
        "year": 1405,
        "exam_code": "1277",
        "booklet_code": "135A",
        "duration_minutes": 250,
        "total_questions": 115,
        "source": {
            "questions_pdf": "assets/source/arshad_computer_1405.pdf",
            "answer_key_pdf": "assets/source/answer_key_computer_1405.pdf",
            "key_status": "official",
        },
        "image_policy": "English questions are structured text. Other questions use adaptive crops containing at most three consecutive questions.",
        "questions": questions,
    }
    computer_path = ROOT / "data/questions/computer_engineering/exam_1405.json"
    computer_path.parent.mkdir(parents=True, exist_ok=True)
    computer_path.write_text(json.dumps(computer_exam, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_key(ROOT / "data/answer_keys/computer_engineering/key_1405.json", "مهندسی کامپیوتر", "1277", "135A", COMPUTER_KEY_MANUAL)

    electrical = json.loads(ELECTRICAL_EXAM.read_text(encoding="utf-8"))
    if len(electrical.get("questions", [])) != 140:
        raise RuntimeError("Electrical exam does not contain 140 questions")
    electrical["answer_key_status"] = "official"
    electrical.setdefault("source", {})["questions_pdf"] = "assets/source/arshad_bargh_1405_1251.pdf"
    electrical["source"]["answer_key_pdf"] = "assets/source/answer_key_electrical_1405.pdf"
    electrical["source"]["key_status"] = "official"
    for question, answer in zip(electrical["questions"], electrical_answers):
        question["correct_answer"] = answer
        question["answer_status"] = "official"
    ELECTRICAL_EXAM.write_text(json.dumps(electrical, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_key(ROOT / "data/answer_keys/key_1405.json", "مهندسی برق", "1251", "335A", electrical_answers)

    # Validation
    assert [item["number"] for item in questions] == list(range(1, 116))
    assert all(item["correct_answer"] in {1, 2, 3, 4} for item in questions)
    assert all((ROOT / item["image"]).exists() for item in questions if "image" in item)
    assert all(item.get("text") and len(item.get("choice_texts", [])) == 4 for item in questions[:25])
    assert all(item["correct_answer"] in {1, 2, 3, 4} for item in electrical["questions"])
    return {
        "computer_questions": 115,
        "computer_text_questions": 25,
        "computer_image_questions": 90,
        "computer_key_answers": 115,
        "electrical_key_answers": 140,
    }


def main() -> None:
    DIAG.mkdir(parents=True, exist_ok=True)
    try:
        summary = build()
        payload = {"success": True, "summary": summary}
    except Exception:
        payload = {"success": False, "error": traceback.format_exc()}
    STATUS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    if not payload["success"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
