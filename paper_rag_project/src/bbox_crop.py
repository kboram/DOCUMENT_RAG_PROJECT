import os
import re
import json
from PIL import Image, ImageDraw

# 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

PAGES_DIR = os.path.join(PROJECT_DIR, "pages")
PARSED_JSON_PATH = os.path.join(PROJECT_DIR, "output", "parsed_result.json")

# 2. parsed_result.json 파일에서 테이블 좌표 가져오기
with open(PARSED_JSON_PATH, 'r', encoding='utf-8') as f:
	json_data = json.load(f)
	
# table 좌표들을 페이지별로 저장할 리스트    
table_bboxes = []
	
# 요소들 확인
for element in json_data["elements"]:
	# 카테고리가 테이블인 경우만 선택하기
	if element["category"] == "table":
		table_bboxes.append({
            "page": element["page"],
            "coordinates": element["coordinates"]
        })
		
# 좌표 개수 확인
print(f"\n총 테이블 개수 : {len(table_bboxes)}")

# 3. 이미지 1개씩 불러와 bbox 표시하고 크롭하기
# 결과 저장할 경로
CROP_DIR = os.path.join(PROJECT_DIR, "crop_results")
os.makedirs(CROP_DIR, exist_ok=True)

# 이미지 파일 하나씩 불러와 처리
image_files = os.listdir(PAGES_DIR)
image_files = [
	f for f in image_files
	if f.lower().endswith(".png")
]

image_files = sorted(
	image_files,
	key = lambda x: int(re.findall(r'\d+', x)[-1])
)

print(f"\n 불러온 이미지 개수 : {len(image_files)}")

for image_name in image_files:
	image_path = os.path.join(PAGES_DIR, image_name)
	# RGB로 변환한 이유 : 이미지마다 색상 형식이 다르기 때문
	image = Image.open(image_path).convert("RGB")
	draw = ImageDraw.Draw(image)
	width, height = image.size

	print(f"이미지 불러옴 : {image_name}, 크기 : {width} x {height}")

	# 페이지 번호 추출
	page_number = int(re.findall(r'\d+', image_name)[-1])
	print(f"\n 페이지 {page_number} 처리 중 : {image_name}")

	# 처리 중인 페이지의 table bbox만 필터링하기
	page_bboxes = [
		bbox for bbox in table_bboxes
		if bbox["page"] == page_number
	]

	# 테이블 번호
	table_idx = 1

	# 해당하는 페이지의 모든 테이블을 처리
	for bbox in page_bboxes:
		coords = bbox["coordinates"]

		xs = [p["x"] for p in coords]
		ys = [p["y"] for p in coords]

		# 픽셀 좌표로 바꾸기
		x_min = int(min(xs) * width)
		y_min = int(min(ys) * height)
		x_max = int(max(xs) * width)
		y_max = int(max(ys) * height)

		# bbox 그리기
		draw.rectangle(
			[(x_min, y_min), (x_max, y_max)],
			outline = "red",
			width = 2
		)

		print(
			f"테이블 {table_idx} bbox : "
			f"({x_min}, {y_min}) ~ ({x_max}, {y_max})"
		)

		# 크롭 단계
		crop_box = (x_min, y_min, x_max, y_max)
		crop_image = image.crop(crop_box)

		# 크롭한 이미지 저장
		crop_name = f"page_{page_number}_table_{table_idx}.png"
		crop_path = os.path.join(CROP_DIR, crop_name)
		crop_image.save(crop_path)

		print(f"크롭 저장 : {crop_name}")

		table_idx += 1

	# bbox가 그려진 이미지 확인
	image.show()