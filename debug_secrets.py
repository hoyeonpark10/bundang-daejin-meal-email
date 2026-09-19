"""
NAVER_EMAIL / NAVER_PASSWORD secret 값이 제대로 들어갔는지(빈 값, 공백 섞임 등)만
확인하는 임시 점검 스크립트. 실제 비밀번호 값은 출력하지 않습니다.
"""

import os


def describe(name):
    value = os.environ.get(name)
    if value is None:
        print(f"{name}: secret 자체가 등록되지 않았습니다 (이름 오타 확인 필요)")
        return

    stripped = value.strip()
    print(f"{name}: 길이={len(value)}자")
    print(f"{name}: 앞뒤 공백/줄바꿈 섞임={value != stripped}")
    print(f"{name}: 빈 문자열 여부={value == ''}")


describe("NAVER_EMAIL")
describe("NAVER_PASSWORD")
describe("RECIPIENT_EMAIL")
