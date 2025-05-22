# test_page_split.py
"""
간단 테스트:
1) 문자열 샘플을 직접 넣어 보거나
2) txt 파일 경로를 인자로 넘겨서 결과를 확인한다.
"""

import sys, textwrap
from services.ebooks2text import split_txt_into_pages   # ↖️ 이미 작성한 함수 그대로 사용

# -------------------------------
# 1. 입력 준비
# -------------------------------
if len(sys.argv) > 1:
    # 사용 예:  python test_page_split.py the_little_prince.txt
    src = sys.argv[1]
    print(f"[INPUT] 파일 모드: {src}")
else:
    # 파일을 넘기지 않으면 하드코딩된 샘플 텍스트 사용
    sample = """
    The Little Prince lived on a small planet that was scarcely bigger than himself,
    and he had need of a friend. For those who are lonely it is a great thing to have
    even a single companion. So the little prince set out on a journey among the stars…
    """ * 300  # 길이를 키우려고 300번 반복
    src = sample.strip()
    print(f"[INPUT] 샘플 문자열 모드 (길이 {len(src)}자)")

# -------------------------------
# 2. 페이지 분할 실행
# -------------------------------
pages = split_txt_into_pages(src)
print(f"\n총 {len(pages)} 페이지 생성\n")

# -------------------------------
# 3. 결과 요약 출력
# -------------------------------
for i, page in enumerate(pages, 1):
    print(f"── Page {i:>2} ── ({len(page)} chars)")
    # 앞·뒤 60자만 미리보기
    head = textwrap.shorten(page[:120].replace("\n", " "), width=80, placeholder="…")
    tail = textwrap.shorten(page[-120:].replace("\n", " "), width=80, placeholder="…")
    print(f"  ↳ 시작: {head}")
    print(f"  ↳ 끝  : {tail}\n")
