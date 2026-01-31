'''
파싱한 파일의 페이지 중 테이블이 포함된 페이지 수 확인
테이블이 포함된 페이지만 이미지로 저장
'''

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
FILE_PATH = os.path.dirname(PROJECT_DIR, "output", "parsed_result.json")
PDF_FILE = os.path.dirname(PROJECT_DIR, "input", "sample_file.pdf")

# 테이블만 불러오기
with open(FILE_PATH, "r", encoding="utf-8") as f:
    parsed_data = json.load(f)

elements = parsed_data.get("elements", [])

tables = [e for e in elements if e.get("category") == "table"]

# 문서 내 테이블 개수 확인
print(f"총 테이블 개수 : {len(tables)}")

# 테이블이 속한 페이지 찾기
table_pages = set()

for e in elements:
    if e.get("category") == "table":
        page = e.get("page") or e.get("page_number")
        table_pages.add(page)

print("테이블이 존재하는 페이지:", sorted(table_pages))


# 해당 페이지만 이미지로 변환
'''
PNG로 선택한 이유
- JPG는 손실 압축이므로 압축 과정에서 선이 흐려지거나 셀 경계가 께질 수 있음
- PNG는 선, 테두리, 작은 글자 보존에 유리하며 좌표 기반 크롭 시 품질 저하 없음
'''
# PyMuPDF 사용
import fitz
doc = fitz.open(PDF_FILE)
table_pages = [1, 9, 10, 11]

# 현재 파일을 기준으로 프로젝트 루트 계산하여 원하는 폴더가 없으면 생성
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

# 원하는 폴더(pages) 경로
PAGE_DIR = os.path.join(PROJECT_ROOT, "pages")
# 없을 때 생성
os.makedirs(PAGE_DIR, exist_ok=True)

for page_num in table_pages:
    page = doc[page_num-1]
    pix = page.get_pixmap()
    pix.save(f"paper_rag_project/pages/page_{page_num}.png")