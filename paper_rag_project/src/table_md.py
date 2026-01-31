'''
크롭한 테이블 이미지를 markdown으로 변환
OCR → 구조 복원 → SLLM → Markdown 저장
'''

import requests
import os
import re
import json
import time
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

load_dotenv()


# 환경 변수
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

CROP_DIR = os.path.join(PROJECT_DIR, "crop_results")
OCR_DIR = os.path.join(PROJECT_DIR, "ocr_results")
MD_DIR = os.path.join(PROJECT_DIR, "md_results")

os.makedirs(OCR_DIR, exist_ok=True)
os.makedirs(MD_DIR, exist_ok=True)


# 유틸
def natural_sort_key(filename):
    return [
        int(x) if x.isdigit() else x
        for x in re.findall(r'\d+|\D+', filename)
    ]


# OCR
OCR_URL = "https://api.upstage.ai/v1/document-digitization"
HEADERS = {"Authorization": f"Bearer {UPSTAGE_API_KEY}"}

def run_ocr(image_path):
    with open(image_path, "rb") as f:
        files = {"document": f}
        data = {"model": "ocr"}
        return requests.post(OCR_URL, headers=HEADERS, files=files, data=data)


def split_row_into_columns(row, x_split=80):
    left = []
    right = []

    for w in row:
        if w["x"] < x_split:
            left.append(w["text"])
        else:
            right.append(w["text"])

    return " ".join(left), " ".join(right)


# OCR → Row 복원
def extract_table_from_ocr(words, y_threshold=6, x_split=80):
    processed = []

    for w in words:
        vertices = w["boundingBox"]["vertices"]
        xs = [v["x"] for v in vertices]
        ys = [v["y"] for v in vertices]

        processed.append({
            "text": w["text"],
            "x": sum(xs) / len(xs),
            "y": sum(ys) / len(ys),
        })

    processed.sort(key=lambda x: x["y"])

    rows = []
    current = []
    current_y = None

    for item in processed:
        if current_y is None or abs(item["y"] - current_y) <= y_threshold:
            current.append(item)
            current_y = item["y"]
        else:
            rows.append(current)
            current = [item]
            current_y = item["y"]

    if current:
        rows.append(current)

    table_rows = []
    for row in rows:
        row = sorted(row, key=lambda x: x["x"])
        left, right = split_row_into_columns(row, x_split)
        if left or right:
            table_rows.append(f"{left} || {right}")

    return table_rows



# 모델 로드 (SLLM)
MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME,
    token=HF_TOKEN
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    token=HF_TOKEN,
    dtype=torch.float16,
    device_map="auto"
)

model.eval()


# Row → Markdown
def rows_to_markdown(rows):
    prompt = f"""
다음은 OCR로부터 복원한 2열 표이다.
각 행은 "왼쪽열 || 오른쪽열" 형식이다.

이를 Markdown table로 변환하라.

규칙:
- 반드시 Markdown table만 출력
- 헤더는 "항목 | 내용"
- 설명 문장 금지

입력:
{chr(10).join(rows)}
"""


    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False
        )

    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    md_lines = [l for l in text.splitlines() if l.strip().startswith("|")]
    return "\n".join(md_lines)


# 실행
image_files = sorted(
    [f for f in os.listdir(CROP_DIR) if f.endswith(".png")],
    key=natural_sort_key
)

for image_name in image_files:
    image_path = os.path.join(CROP_DIR, image_name)
    base = os.path.splitext(image_name)[0]
    ocr_path = os.path.join(OCR_DIR, f"{base}.json")

    if not os.path.exists(ocr_path):
        print(f"OCR 처리 중: {image_name}")
        res = run_ocr(image_path)
        if res.status_code != 200:
            print("OCR 실패")
            continue
        with open(ocr_path, "w", encoding="utf-8") as f:
            json.dump(res.json(), f, ensure_ascii=False, indent=2)
        time.sleep(2)

    with open(ocr_path, "r", encoding="utf-8") as f:
        ocr_json = json.load(f)

    words = ocr_json["pages"][0]["words"]
    rows = extract_table_from_ocr(words)

    md = rows_to_markdown(rows)

    md_path = os.path.join(MD_DIR, f"{base}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Markdown 저장 완료: {md_path}")
    time.sleep(1)
