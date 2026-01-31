# Upstage Document Parsing API로 문서 파싱 후 결과 보기

import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

api_key = os.getenv("UPSTAGE_API_KEY")
filename = "paper_rag_project/input/sample_file.pdf"
OUTPUT_DIR = "paper_rag_project/output"
OUTPUT_FILE = "parsed_result.json"

url = "https://api.upstage.ai/v1/document-digitization"
headers = {"Authorization": f"Bearer {api_key}"}
files = {"document": open(filename, "rb")}
data = {"ocr": "force", "base64_encoding": "['table']", "model": "document-parse"}
response = requests.post(url, headers=headers, files=files, data=data)

# 터미널에서 확인
print(response.json())

# 응답 JSON 변환
result = response.json()

# 파일로 저장
output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"파싱 결과 저장 완료 : {output_path}")